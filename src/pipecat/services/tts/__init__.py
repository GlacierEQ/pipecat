"""
Text-to-speech services for pipecat.

This module provides integrations with various text-to-speech APIs and services.
"""

from ..elevenlabs import ElevenLabsTTSService
from ..azure import AzureTTSService
from ..cartesia import CartesiaTTSService
from ..deepgram import DeepgramTTSService

__all__ = ["ElevenLabsTTSService", "AzureTTSService", "CartesiaTTSService", "DeepgramTTSService"]
