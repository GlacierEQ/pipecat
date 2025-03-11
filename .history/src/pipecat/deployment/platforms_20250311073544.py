"""
Platform-specific deployment utilities for Pipecat applications.
"""
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List


class Deployer(ABC):
    """Base class for platform-specific deployers."""
    
    @abstractmethod
    def deploy(self, app_path: str, **kwargs) -> bool:
        """Deploy the application to the target platform."""
        pass
    
    @abstractmethod
    def get_status(self, app_name: str) -> Dict[str, Any]:
        """Get the status of a deployed application."""
        pass


class FlyIODeployer(Deployer):
    """Deployer for Fly.io platform."""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.environ.get("FLY_API_TOKEN")
    
    def deploy(self, app_path: str, **kwargs) -> bool:
        """Deploy the application to Fly.io."""
        app_name = kwargs.get("app_name")
        region = kwargs.get("region", "sjc")
        
        env_vars = kwargs.get("env_vars", {})
        env_args = []
        for key, value in env_vars.items():
            env_args.extend(["--env", f"{key}={value}"])
        
        cmd = [
            "fly", "launch",
            "--name", app_name,
            "--region", region
        ] + env_args
        
        try:
            subprocess.run(cmd, check=True, cwd=app_path)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error deploying to Fly.io: {e}")
            return False
    
    def get_status(self, app_name: str) -> Dict[str, Any]:
        """Get the status of a deployed application on Fly.io."""
        try:
            result = subprocess.run(
                ["fly", "status", "-a", app_name],
                check=True,
                capture_output=True,
                text=True
            )
            # Parse the output to extract status information
            status = {"status": "running" if "is running" in result.stdout else "stopped"}
            return status
        except subprocess.CalledProcessError as e:
            print(f"Error getting status from Fly.io: {e}")
            return {"status": "unknown", "error": str(e)}


class ModalDeployer(Deployer):
    """Deployer for Modal platform."""
    
    def deploy(self, app_path: str, **kwargs) -> bool:
        """Deploy the application to Modal."""
        # Modal-specific deployment logic
        try:
            subprocess.run(
                ["modal", "deploy", app_path],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error deploying to Modal: {e}")
            return False
    
    def get_status(self, app_name: str) -> Dict[str, Any]:
        """Get the status of a deployed application on Modal."""
        try:
            result = subprocess.run(
                ["modal", "app", "show", app_name],
                check=True,
                capture_output=True,
                text=True
            )
            # Parse the output to extract status information
            return {"status": "running" if "running" in result.stdout else "stopped"}
        except subprocess.CalledProcessError as e:
            return {"status": "unknown", "error": str(e)}


class HerokuDeployer(Deployer):
    """Deployer for Heroku platform."""
    
    def deploy(self, app_path: str, **kwargs) -> bool:
        """Deploy the application to Heroku."""
        app_name = kwargs.get("app_name")
        
        try:
            # Initialize Git if not already initialized
            git_dir = Path(app_path) / ".git"
            if not git_dir.exists():
                subprocess.run(["git", "init"], cwd=app_path, check=True)
            
            # Create Heroku app if it doesn't exist
            try:
                subprocess.run(
                    ["heroku", "apps:info", app_name],
                    check=True, 
                    stdout=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                subprocess.run(
                    ["heroku", "create", app_name],
                    check=True,
                    cwd=app_path
                )
            
            # Set environment variables
            env_vars = kwargs.get("env_vars", {})
            for key, value in env_vars.items():
                subprocess.run(
                    ["heroku", "config:set", f"{key}={value}", "-a", app_name],
                    check=True
                )
            
            # Deploy to Heroku
            subprocess.run(
                ["git", "add", "."],
                cwd=app_path,
                check=True
            )
            try:
                subprocess.run(
                    ["git", "commit", "-m", "Deploy to Heroku"],
                    cwd=app_path,
                    check=True
                )
            except subprocess.CalledProcessError:
                # Ignore error if there's nothing to commit
                pass
            
            subprocess.run(
                ["git", "push", "heroku", "main"],
                cwd=app_path,
                check=True
            )
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error deploying to Heroku: {e}")
            return False
    
    def get_status(self, app_name: str) -> Dict[str, Any]:
        """Get the status of a deployed application on Heroku."""
        try:
            result = subprocess.run(
                ["heroku", "ps", "-a", app_name],
                check=True,
                capture_output=True,
                text=True
            )
            return {"status": "running" if "up" in result.stdout else "stopped"}
        except subprocess.CalledProcessError as e:
            return {"status": "unknown", "error": str(e)}
