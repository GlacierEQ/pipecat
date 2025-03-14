# Pipecat

<img src="assets/images/pipecat.png" width="150" alt="Pipecat Logo">

**Real-time AI pipelines for complex AI communications stacks**

## Overview

Pipecat is a framework for building real-time AI applications with a focus on audio, video, and text processing pipelines. It provides a unified interface for connecting various AI services and handling real-time data flows.

## Features

- **Real-time processing** of audio, video, and text data
- **Modular architecture** for easy extension and customization
- **Service abstractions** for popular AI providers (OpenAI, Anthropic, Google, etc.)
- **Transport layers** for various communication protocols (WebSockets, HTTP, etc.)
- **Asynchronous by default** for high performance
- **Built-in monitoring** and metrics

## Installation

```shell
pip install pipecat-ai
```

To include optional dependencies:

```shell
pip install "pipecat-ai[llm,tts,stt]"
```

For development:

```shell
pip install "pipecat-ai[all]"
```

## Quick Start

```python
from pipecat.api import Pipeline, PipelineTask
from pipecat.services.llm import OpenAILLMService
from pipecat.services.stt import DeepgramSTTService
from pipecat.services.tts import ElevenLabsTTSService

# Create a simple voice assistant pipeline
pipeline = Pipeline([
    # Process audio input
    DeepgramSTTService(),
    # Generate AI response
    OpenAILLMService(model="gpt-4"),
    # Convert to speech
    ElevenLabsTTSService(voice_id="your-voice-id")
])

# Run the pipeline
pipeline.run()
```

## Code examples

- [Foundational](https://github.com/pipecat-ai/pipecat/tree/main/examples/foundational) — small snippets that build on each other, introducing one or two concepts at a time
- [Example apps](https://github.com/pipecat-ai/pipecat/tree/main/examples/) — complete applications that you can use as starting points for development

## Project Structure

```
pipecat/
├── assets/            # Project assets (images, etc.)
├── config/            # Configuration files
├── docker/            # Docker-related files
├── docs/              # Documentation
│   ├── api/           # API documentation
│   ├── images/        # Documentation images
│   └── markdown/      # Markdown documentation
├── examples/          # Example applications
├── scripts/           # Utility scripts
├── src/               # Source code
│   └── pipecat/       # Main package
│       ├── api/       # Public API
│       ├── cli/       # Command-line interface
│       ├── config/    # Configuration management
│       ├── core/      # Core functionality
│       └── ...        # Other modules
└── tests/             # Test suite
```

## Hacking on the framework itself

_Note: You may need to set up a virtual environment before following these instructions. From the root of the repo:_

```shell
python3 -m venv venv
source venv/bin/activate
```

Install the development dependencies:

```shell
pip install -r dev-requirements.txt
```

Install the git pre-commit hooks (these help ensure your code follows project rules):

```shell
pre-commit install
```

Install the `pipecat-ai` package locally in editable mode:

```shell
pip install -e .
```

## License

MIT
