# Pipecat Architecture

This document describes the high-level architecture of the Pipecat framework.

## Overview

Pipecat is designed as a modular pipeline system for AI applications, focused on real-time processing of audio, text, and other media formats. The architecture follows these core principles:

- **Pipeline-based processing**: Data flows through series of processors
- **Frame-based communication**: All data is encapsulated in typed frames
- **Asynchronous by default**: Built for non-blocking I/O operations
- **Service abstraction**: Common interface for various AI services
- **Extensibility**: Easily add new components and services

## Core Components

### 1. Frames

Frames are the fundamental data units that flow through pipelines. Each frame represents a specific piece of information or event:

- **SystemFrames**: Control pipeline operation (Start, End, Cancel)
- **MediaFrames**: Contain audio, video, or images
- **TextFrames**: Contain text data (transcriptions, LLM responses)
- **MetricFrames**: Provide performance and diagnostics data

### 2. Processors

Processors are components that manipulate frames as they pass through:

- **Input processors**: Generate frames from external sources
- **Transform processors**: Modify frame data
- **Aggregator processors**: Combine multiple frames
- **Output processors**: Send frames to external destinations

### 3. Pipeline

The pipeline connects processors together and manages frame flow:

- **Pipeline**: Linear sequence of processors
- **ParallelPipeline**: Splits processing across multiple paths
- **SyncParallelPipeline**: Synchronizes parallel processing

### 4. Services

Services connect to external APIs and systems:

- **LLM Services**: OpenAI, Anthropic, Google, etc.
- **TTS Services**: ElevenLabs, Azure, etc.
- **STT Services**: Deepgram, Whisper, etc.
- **Transport Services**: WebRTC, WebSocket, etc.

### 5. Transports

Transports handle external I/O:

- **Network transports**: WebSocket, HTTP
- **Service transports**: Daily, LiveKit
- **Local transports**: File system, microphone/speakers

## Directory Structure

```
src/pipecat/
├── api/           # Public API interfaces
├── cli/           # Command-line interface
├── config/        # Configuration management
├── core/          # Core functionality and base classes
├── frames/        # Frame definitions
├── metrics/       # Metrics collection and reporting
├── models/        # Data models and schemas
├── pipeline/      # Pipeline implementation
├── processors/    # Frame processors
│   ├── aggregators/  # Frame aggregation processors
│   ├── filters/      # Frame filtering processors
│   └── frameworks/   # Integration with external frameworks
├── services/      # External service integrations
│   ├── llm/       # Language model services
│   ├── stt/       # Speech-to-text services
│   └── tts/       # Text-to-speech services
├── transports/    # I/O transport implementations
└── utils/         # Utility functions and helpers
```

## Flow Diagram

```
Input → Processors → Output
  ↑         ↓         ↓
  ↑    ┌────┴────┐    ↓
  └────┤ Services ├────┘
       └─────────┘
```

## Extension Points

Pipecat is designed to be extended in several ways:

1. **Custom Processors**: Create new frame processors
2. **Custom Frames**: Define new frame types
3. **Service Integrations**: Add new AI service providers
4. **Transport Layers**: Support new communication protocols
5. **Pipeline Topologies**: Create specialized pipeline structures
