"""
Speech-to-text services for pipecat.

This module provides integrations with various speech-to-text APIs and services.
"""

from ..deepgram import DeepgramSTTService
from ..whisper import WhisperSTTService
from ..azure import AzureSTTService

__all__ = ["DeepgramSTTService", "WhisperSTTService", "AzureSTTService"]
