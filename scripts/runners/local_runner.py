#!/usr/bin/env python3
"""
Local development runner for Pipecat applications.

This script provides a convenient way to run Pipecat applications
locally with hot-reloading for development purposes.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pipecat.config import default_config


class PipecatFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        self.last_modified = time.time()
        
    def on_modified(self, event):
        if event.src_path.endswith(".py") and time.time() - self.last_modified > 1:
            self.last_modified = time.time()
            self.callback()


def main():
    parser = argparse.ArgumentParser(description="Pipecat Local Development Runner")
    parser.add_argument("path", help="Path to the Pipecat application to run")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reloading")
    parser.add_argument("--log-level", default=default_config.log_level, help="Set log level")
    
    args = parser.parse_args()
    
    app_path = Path(args.path)
    if not app_path.exists():
        print(f"Error: Could not find {app_path}")
        return 1
    
    os.environ["PIPECAT_LOG_LEVEL"] = args.log_level
    
    def run_app():
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting Pipecat application...")
        try:
            if app_path.is_file():
                # Execute the file
                exec(open(app_path).read())
            else:
                # Import and run module
                sys.path.insert(0, str(app_path.parent))
                module_name = app_path.name
                __import__(module_name)
        except Exception as e:
            print(f"Error running application: {e}")
    
    run_app()
    
    if not args.no_reload:
        print("Watching for file changes (Ctrl+C to quit)...")
        event_handler = PipecatFileHandler(run_app)
        observer = Observer()
        observer.schedule(event_handler, ".", recursive=True)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    return 0


if __name__ == "__main__":
    sys.exit(main())
