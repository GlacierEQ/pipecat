"""
Gemini API integration for Pipecat LLM service.

This module provides a Gemini-based LLM service implementation that can be used
as an alternative to OpenAI's API.
"""
import asyncio
from typing import Dict, List, Optional, Union, Any
import logging
import os

try:
    import google.generativeai as genai
    from google.generativeai import GenerationConfig
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from ...frames import TextFrame, Frame
from ...pipeline import PipelineTask


class GeminiLLMService(PipelineTask):
    """
    Gemini LLM service for generating text using Google's Gemini API.
    
    This service can be used as a drop-in replacement for OpenAI-based LLM services.
    """
    
    def __init__(
        self,
        model: str = "gemini-pro",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 40,
        safety_settings: Optional[Dict[str, str]] = None,
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize the Gemini LLM service.
        
        Args:
            model: Gemini model to use (gemini-pro, gemini-pro-vision)
            api_key: Gemini API key (defaults to GOOGLE_API_KEY env var)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            safety_settings: Safety settings for content filtering
            system_prompt: System prompt to initialize the conversation
        """
        super().__init__()
        self.name = "GeminiLLM"
        self.model = model
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.top_k = top_k
        self.safety_settings = safety_settings or {}
        self.system_prompt = system_prompt
        self.logger = logging.getLogger("pipecat.llm.gemini")
        
        if not GEMINI_AVAILABLE:
            self.logger.warning(
                "Google Generative AI package not available. "
                "Install with: pip install google-generativeai"
            )
        
        self._initialize_gemini()
    
    def _initialize_gemini(self) -> None:
        """Initialize the Gemini client."""
        if not GEMINI_AVAILABLE or not self.api_key:
            return
        
        genai.configure(api_key=self.api_key)
        
        # Set up generation config
        self.generation_config = GenerationConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            max_output_tokens=self.max_tokens,
        )
        
        # Create model
        self.gemini_model = genai.GenerativeModel(
            model_name=self.model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )
        
        # Initialize chat if system prompt is provided
        if self.system_prompt:
            self.chat_session = self.gemini_model.start_chat(
                history=[{"role": "system", "parts": [self.system_prompt]}]
            )
        else:
            self.chat_session = self.gemini_model.start_chat()
    
    async def process(self, frame: Frame) -> Frame:
        """
        Process a frame using the Gemini LLM service.
        
        Args:
            frame: Input frame to process
            
        Returns:
            Processed frame with LLM response
        """
        if not isinstance(frame, TextFrame):
            self.logger.warning(f"GeminiLLMService can only process TextFrames, got {type(frame)}")
            return frame
        
        if not GEMINI_AVAILABLE:
            self.logger.error("Gemini API not available. Skipping LLM processing.")
            return frame
        
        if not self.api_key:
            self.logger.error("No Gemini API key provided. Skipping LLM processing.")
            return frame
        
        # Extract relevant information
        prompt = frame.text
        source = frame.source or "user"
        
        # Process with Gemini asynchronously
        response = await self._generate_response(prompt, source)
        
        # Create response frame
        if response:
            response_frame = TextFrame(
                text=response,
                source="gemini",
                metadata={
                    "model": self.model,
                    "parent_id": frame.id,
                    "temperature": self.temperature
                }
            )
            return response_frame
        
        # Return original frame if processing failed
        return frame
    
    async def _generate_response(self, prompt: str, role: str = "user") -> Optional[str]:
        """
        Generate a response from Gemini asynchronously.
        
        Args:
            prompt: Text prompt for the model
            role: Role for the prompt (user, assistant)
            
        Returns:
            Generated text response or None if generation failed
        """
        try:
            # Run in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._generate_response_sync,
                prompt,
                role
            )
            return response
        except Exception as e:
            self.logger.error(f"Error generating response from Gemini: {e}")
            return None
    
    def _generate_response_sync(self, prompt: str, role: str = "user") -> Optional[str]:
        """
        Generate a response synchronously.
        
        Args:
            prompt: Text prompt for the model
            role: Role for the prompt
            
        Returns:
            Generated text response
        """
        try:
            if hasattr(self, 'chat_session'):
                # Add the message to the chat and get a response
                response = self.chat_session.send_message(prompt)
                return response.text
            else:
                # Generate a one-off response
                response = self.gemini_model.generate_content(prompt)
                return response.text
        except Exception as e:
            self.logger.error(f"Error in Gemini synchronous generation: {e}")
            return None
