"""
Batch processing utilities for optimizing pipeline throughput.
"""
from typing import List, TypeVar, Generic, Callable, Any, Optional, Dict
import asyncio
import time
from dataclasses import dataclass, field


T = TypeVar('T')
U = TypeVar('U')


@dataclass
class Batch(Generic[T]):
    """A batch of items to be processed together."""
    
    items: List[T]
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BatchProcessor(Generic[T, U]):
    """Process items in batches for better efficiency."""
    
    def __init__(
        self,
        process_fn: Callable[[List[T]], List[U]],
        max_batch_size: int = 32,
        max_wait_time: float = 0.1
    ):
        """
        Initialize the batch processor.
        
        Args:
            process_fn: Function that processes a batch of items
            max_batch_size: Maximum number of items in a batch
            max_wait_time: Maximum time to wait for a batch to fill up (seconds)
        """
        self.process_fn = process_fn
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        
        self._current_batch: List[T] = []
        self._batch_lock = asyncio.Lock()
        self._batch_event = asyncio.Event()
        self._last_item_time = time.time()
        self._processing = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the batch processor."""
        if self._processing:
            return
        
        self._processing = True
        self._task = asyncio.create_task(self._process_loop())
    
    async def stop(self):
        """Stop the batch processor."""
        if not self._processing:
            return
        
        self._processing = False
        if self._task:
            self._batch_event.set()  # Wake up the processing loop
            await self._task
            self._task = None
    
    async def process(self, item: T) -> U:
        """
        Process an item by adding it to a batch.
        
        Args:
            item: Item to process
            
        Returns:
            Processed result
        """
        # Create a future to hold the result
        future = asyncio.Future()
        
        # Add the item and its future to the current batch
        async with self._batch_lock:
            self._current_batch.append((item, future))
            self._last_item_time = time.time()
            
            # If the batch is full, notify the processing loop
            if len(self._current_batch) >= self.max_batch_size:
                self._batch_event.set()
        
        # Wait for the result
        return await future
    
    async def _process_loop(self):
        """Main processing loop for batches."""
        while self._processing:
            # Wait for a batch to be ready
            await self._wait_for_batch()
            
            if not self._processing:
                break
            
            # Get the current batch
            async with self._batch_lock:
                if not self._current_batch:
                    continue
                
                batch_to_process = self._current_batch
                self._current_batch = []
                self._batch_event.clear()
            
            # Process the batch
            try:
                items, futures = zip(*batch_to_process)
                results = await asyncio.to_thread(self.process_fn, list(items))
                
                # Set results for futures
                for future, result in zip(futures, results):
                    future.set_result(result)
            except Exception as e:
                # Set exception for all futures
                for _, future in batch_to_process:
                    if not future.done():
                        future.set_exception(e)
    
    async def _wait_for_batch(self):
        """Wait for a batch to be ready for processing."""
        # Wait for either the batch to be full or the timeout
        timeout_task = asyncio.create_task(asyncio.sleep(self.max_wait_time))
        event_task = asyncio.create_task(self._batch_event.wait())
        
        done, pending = await asyncio.wait(
            [timeout_task, event_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel the remaining task
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


class DynamicBatcher(Generic[T, U]):
    """
    Adaptive batch processor that dynamically adjusts batch size based on performance.
    """
    
    def __init__(
        self,
        process_fn: Callable[[List[T]], List[U]],
        initial_batch_size: int = 16,
        min_batch_size: int = 1,
        max_batch_size: int = 128,
        target_latency: float = 0.1,
        adjustment_factor: float = 1.2
    ):
        """
        Initialize the dynamic batcher.
        
        Args:
            process_fn: Function that processes a batch of items
            initial_batch_size: Starting batch size
            min_batch_size: Minimum batch size
            max_batch_size: Maximum batch size
            target_latency: Target processing latency in seconds
            adjustment_factor: Factor by which to adjust batch size
        """
        self.process_fn = process_fn
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.target_latency = target_latency
        self.adjustment_factor = adjustment_factor
        
        self._current_batch_size = initial_batch_size
        self._batch_processor = BatchProcessor(
            process_fn=self._process_batch_with_metrics,
            max_batch_size=self._current_batch_size,
            max_wait_time=target_latency / 2
        )
        
        # Metrics for adjusting batch size
        self._last_batch_latency = 0.0
        self._batch_history: List[float] = []
        self._history_size = 10
    
    async def start(self):
        """Start the dynamic batcher."""
        await self._batch_processor.start()
    
    async def stop(self):
        """Stop the dynamic batcher."""
        await self._batch_processor.stop()
    
    async def process(self, item: T) -> U:
        """
        Process an item using dynamic batching.
        
        Args:
            item: Item to process
            
        Returns:
            Processed result
        """
        return await self._batch_processor.process(item)
    
    def _process_batch_with_metrics(self, items: List[T]) -> List[U]:
        """
        Process a batch and collect performance metrics.
        
        Args:
            items: Batch of items to process
            
        Returns:
            Batch of processed results
        """
        start_time = time.time()
        
        results = self.process_fn(items)
        
        # Calculate and store latency
        latency = time.time() - start_time
        self._last_batch_latency = latency
        
        # Add to history and keep only the most recent entries
        self._batch_history.append(latency)
        if len(self._batch_history) > self._history_size:
            self._batch_history.pop(0)
        
        # Adjust batch size based on latency
        self._adjust_batch_size()
        
        return results
    
    def _adjust_batch_size(self):
        """Adjust batch size based on recent performance."""
        if not self._batch_history:
            return
        
        # Calculate average latency
        avg_latency = sum(self._batch_history) / len(self._batch_history)
        
        # Adjust batch size
        if avg_latency > self.target_latency * 1.1:  # Too slow
            new_size = max(
                self.min_batch_size,
                int(self._current_batch_size / self.adjustment_factor)
            )
        elif avg_latency < self.target_latency * 0.9:  # Too fast
            new_size = min(
                self.max_batch_size,
                int(self._current_batch_size * self.adjustment_factor)
            )
        else:  # Just right
            return
        
        # Update batch size if it changed
        if new_size != self._current_batch_size:
            self._current_batch_size = new_size
            self._batch_processor.max_batch_size = new_size
