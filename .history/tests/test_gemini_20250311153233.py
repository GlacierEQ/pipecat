import os

import pytest

from pipecat.frames import TextFrame
from pipecat.services.llm import GeminiLLMService


# Skip tests if Gemini API key is not set
@pytest.mark.skipif(os.environ.get("GOOGLE_API_KEY") is None, reason="Missing GOOGLE_API_KEY environment variable")
@pytest.mark.asyncio
async def test_gemini_llm_service():
    """Test the Gemini LLM service."""
    # Initialize Gemini service
    gemini_service = GeminiLLMService(api_key=os.environ.get("GOOGLE_API_KEY"))
    
    # Create a test frame
    test_frame = TextFrame(text="Tell me a joke.", source="test")
    
    # Process the frame
    result_frame = await gemini_service.process(test_frame)
    
    # Assert that the result frame is not None
    assert result_frame is not None
    
    # Assert that the result frame contains text
    assert result_frame.text is not None
    assert isinstance(result_frame.text, str)
    
    # Assert that the source is Gemini
    assert result_frame.source == "gemini"
