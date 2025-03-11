"""
Command-line interface for pipecat.

This module provides command-line tools for working with pipecat applications
including creating new projects, running examples, and managing resources.
"""

import argparse
import sys
from typing import List

from .dashboard import dashboard_main


def main(args: List[str] = None) -> int:
    """Entry point for the pipecat CLI."""
    if args is None:
        args = sys.argv[1:]
        
    parser = argparse.ArgumentParser(description="Pipecat CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create new project command
    new_parser = subparsers.add_parser("new", help="Create a new pipecat project")
    new_parser.add_argument("name", help="Name of the project")
    new_parser.add_argument(
        "--template", 
        choices=["basic", "chatbot", "voice", "multimodal"], 
        default="basic",
        help="Template to use"
    )
    
    # Run example command
    example_parser = subparsers.add_parser("example", help="Run an example")
    example_parser.add_argument("name", help="Name of the example to run")
    
    # Dashboard command - just pass through to the dashboard module
    dashboard_parser = subparsers.add_parser("dashboard", help="Launch the Pipecat dashboard")
    dashboard_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    dashboard_parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    dashboard_parser.add_argument("--theme", choices=["light", "dark"], default="light", help="Dashboard theme")
    
    # Parse args and dispatch
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command == "new":
        return create_new_project(parsed_args.name, parsed_args.template)
    elif parsed_args.command == "example":
        return run_example(parsed_args.name)
    elif parsed_args.command == "dashboard":
        # Extract dashboard args and pass to dashboard_main
        dashboard_args = []
        if parsed_args.host:
            dashboard_args.extend(["--host", parsed_args.host])
        if parsed_args.port:
            dashboard_args.extend(["--port", str(parsed_args.port)])
        if parsed_args.theme:
            dashboard_args.extend(["--theme", parsed_args.theme])
        return dashboard_main(dashboard_args)
    else:
        parser.print_help()
        return 1


def create_new_project(name: str, template: str) -> int:
    """Create a new project from a template."""
    print(f"Creating new project '{name}' using template '{template}'")
    # Implementation would go here
    return 0


def run_example(name: str) -> int:
    """Run a named example."""
    print(f"Running example '{name}'")
    # Implementation would go here
    return 0


if __name__ == "__main__":
    sys.exit(main())
