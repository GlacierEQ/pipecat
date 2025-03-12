"""
Caching utilities for optimizing pipeline performance.
"""
import os
import pickle
import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, TypeVar, Generic, Union
from pathlib import Path
import threading
import tempfile

T = TypeVar('T')


class ResultCache(ABC, Generic[T]):
    """Abstract base class for result caches."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Get a cached result."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set a cached result."""
        pass
    
    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        pass
    
    @abstractmethod
    def invalidate(self, key: str) -> bool:
        """Invalidate a cached result."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the entire cache."""
        pass
    
    def get_or_compute(self, key: str, compute_fn: Callable[[], T], ttl: Optional[int] = None) -> T:
        """Get from cache or compute and cache the result."""
        if self.has(key):
            return self.get(key)
        
        value = compute_fn()
        self.set(key, value, ttl)
        return value


class MemoryCache(ResultCache[T]):
    """In-memory implementation of ResultCache."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        """Get a cached result."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check if expired
            if key in self._expiry and time.time() > self._expiry[key]:
                self.invalidate(key)
                return None
            
            # Update access time for LRU
            self._access_times[key] = time.time()
            
            return self._cache[key]
    
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set a cached result."""
        with self._lock:
            # If cache is full, remove least recently used item
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = value
            self._access_times[key] = time.time()
            
            if ttl is not None:
                self._expiry[key] = time.time() + ttl
    
    def has(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        with self._lock:
            if key not in self._cache:
                return False
            
            # Check if expired
            if key in self._expiry and time.time() > self._expiry[key]:
                self.invalidate(key)
                return False
            
            return True
    
    def invalidate(self, key: str) -> bool:
        """Invalidate a cached result."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._expiry.pop(key, None)
                self._access_times.pop(key, None)
                return True
            return False
    
    def clear(self) -> None:
        """Clear the entire cache."""
        with self._lock:
            self._cache.clear()
            self._expiry.clear()
            self._access_times.clear()
    
    def _evict_lru(self) -> None:
        """Evict the least recently used item from the cache."""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        self.invalidate(lru_key)


class PersistentCache(ResultCache[T]):
    """File-based persistent implementation of ResultCache."""
    
    def __init__(self, cache_dir: Optional[str] = None, max_size_mb: int = 100):
        """
        Initialize a persistent cache.
        
        Args:
            cache_dir: Directory to store cache files (defaults to environment variable or temp dir)
            max_size_mb: Maximum cache size in MB
        """
        # Use environment variable PIPECAT_CACHE_DIR if available, otherwise use provided or temp dir
        if cache_dir is None:
            cache_dir = os.environ.get(
                "PIPECAT_CACHE_DIR", 
                os.path.join(tempfile.gettempdir(), "pipecat_cache")
            )
        
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._metadata_path = self.cache_dir / "metadata.json"
        self._lock = threading.RLock()
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load metadata
        self._metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from disk."""
        if not self._metadata_path.exists():
            return {"items": {}}
        
        try:
            with open(self._metadata_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"items": {}}
    
    def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        with open(self._metadata_path, "w") as f:
            json.dump(self._metadata, f)
    
    def _get_path(self, key: str) -> Path:
        """Get the path for a cache item."""
        # Use a hash of the key as the filename to avoid invalid chars
        filename = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / filename
    
    def get(self, key: str) -> Optional[T]:
        """Get a cached result."""
        with self._lock:
            if key not in self._metadata["items"]:
                return None
            
            item_meta = self._metadata["items"][key]
            
            # Check if expired
            if "expires" in item_meta and time.time() > item_meta["expires"]:
                self.invalidate(key)
                return None
            
            # Load the item
            try:
                with open(self._get_path(key), "rb") as f:
                    value = pickle.load(f)
                
                # Update access time
                self._metadata["items"][key]["last_access"] = time.time()
                self._save_metadata()
                
                return value
            except (IOError, pickle.PickleError):
                # If there's an error loading, invalidate the item
                self.invalidate(key)
                return None
    
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set a cached result."""
        with self._lock:
            # Check if we need to make room
            self._ensure_space()
            
            # Save the item
            path = self._get_path(key)
            with open(path, "wb") as f:
                pickle.dump(value, f)
            
            # Update metadata
            item_meta = {
                "created": time.time(),
                "last_access": time.time(),
                "size": path.stat().st_size
            }
            
            if ttl is not None:
                item_meta["expires"] = time.time() + ttl
            
            self._metadata["items"][key] = item_meta
            self._save_metadata()
    
    def has(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        with self._lock:
            if key not in self._metadata["items"]:
                return False
            
            item_meta = self._metadata["items"][key]
            
            # Check if expired
            if "expires" in item_meta and time.time() > item_meta["expires"]:
                self.invalidate(key)
                return False
            
            # Check if file exists
            if not self._get_path(key).exists():
                self.invalidate(key)
                return False
            
            return True
    
    def invalidate(self, key: str) -> bool:
        """Invalidate a cached result."""
        with self._lock:
            if key not in self._metadata["items"]:
                return False
            
            # Delete the file
            try:
                self._get_path(key).unlink(missing_ok=True)
            except IOError:
                pass
            
            # Update metadata
            del self._metadata["items"][key]
            self._save_metadata()
            
            return True
    
    def clear(self) -> None:
        """Clear the entire cache."""
        with self._lock:
            # Delete all cache files
            for key in list(self._metadata["items"].keys()):
                self._get_path(key).unlink(missing_ok=True)
            
            # Reset metadata
            self._metadata = {"items": {}}
            self._save_metadata()
    
    def _ensure_space(self) -> None:
        """Ensure there's enough space in the cache."""
        # Calculate current size
        current_size = sum(
            item.get("size", 0) for item in self._metadata["items"].values()
        )
        
        # If we're under the limit, we're good
        if current_size <= self.max_size_bytes:
            return
        
        # Sort items by last access time
        items = sorted(
            ((k, v) for k, v in self._metadata["items"].items()),
            key=lambda x: x[1].get("last_access", 0)
        )
        
        # Delete items until we're under the limit
        for key, item in items:
            self.invalidate(key)
            current_size -= item.get("size", 0)
            if current_size <= self.max_size_bytes * 0.8:  # Aim for 80% usage
                break
