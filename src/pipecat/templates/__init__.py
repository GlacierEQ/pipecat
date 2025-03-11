"""
Project templates and scaffolding for Pipecat.

This module provides templates for quickly bootstrapping new Pipecat projects
and examples with best-practice structure and configurations.
"""

from .scaffold import create_project, available_templates, TemplateError

__all__ = ["create_project", "available_templates", "TemplateError"]
