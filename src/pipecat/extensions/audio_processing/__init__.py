"""
High-performance audio processing extensions.

This module provides optimized implementations of audio processing
algorithms using C++ and pybind11.
"""
import numpy as np

try:
    from ._audio_processing import apply_gain
except ImportError:
    import warnings
    warnings.warn("Audio processing extensions not available, falling back to Python implementation")
    
    # Fallback Python implementation
    def apply_gain(audio, gain=1.0):
        """Apply gain to audio (Python fallback implementation)."""
        return np.array(audio) * gain

__all__ = ["apply_gain"]
