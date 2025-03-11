"""
Command-line interface for launching the Pipecat dashboard.
"""
import argparse
import asyncio
import sys
import os
from typing import List
import uvicorn

from ..web.dashboard import Dashboard, DashboardConfig


def dashboard_main(args: List[str] = None) -> int:
    """
    Entry point for the pipecat dashboard CLI command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code
    """
    if args is None:
        args = sys.argv[1:]
    
    parser = argparse.ArgumentParser(description="Pipecat Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--theme", choices=["light", "dark"], default="light", help="Dashboard theme")
    parser.add_argument("--title", default="Pipecat Dashboard", help="Dashboard title")
    parser.add_argument("--custom-css", help="Path to custom CSS file")
    parser.add_argument("--custom-js", help="Path to custom JavaScript file")
    parser.add_argument("--no-metrics", action="store_false", dest="enable_metrics", help="Disable metrics")
    parser.add_argument("--no-logs", action="store_false", dest="enable_logs", help="Disable logs")
    parser.add_argument("--no-pipeline-vis", action="store_false", dest="enable_pipeline_vis", help="Disable pipeline visualization")
    
    parsed_args = parser.parse_args(args)
    
    # Create dashboard configuration
    config = DashboardConfig(
        title=parsed_args.title,
        theme=parsed_args.theme,
        custom_css=parsed_args.custom_css,
        custom_js=parsed_args.custom_js,
        enable_metrics=parsed_args.enable_metrics,
        enable_logs=parsed_args.enable_logs,
        enable_pipeline_vis=parsed_args.enable_pipeline_vis,
    )
    
    # Create and run dashboard
    dashboard = Dashboard(config=config)
    
    print(f"Starting Pipecat dashboard at http://{parsed_args.host}:{parsed_args.port}")
    uvicorn.run(dashboard.app, host=parsed_args.host, port=parsed_args.port)
    
    return 0


if __name__ == "__main__":
    sys.exit(dashboard_main())
