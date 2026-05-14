#!/usr/bin/env python3
"""
Docker-based deployment script for Pipecat applications.

This script automates the deployment of Pipecat using Docker or Docker Compose.
"""
import argparse
import os
import subprocess
import sys
import time
import shutil
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy Pipecat using Docker",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Main deployment mode
    parser.add_argument(
        "mode", 
        choices=["compose", "docker", "swarm", "kubernetes"],
        help="Deployment mode"
    )
    
    # Docker options
    parser.add_argument(
        "--tag", 
        default="latest",
        help="Docker image tag"
    )
    
    parser.add_argument(
        "--build-type", 
        choices=["Debug", "Release"],
        default="Release",
        help="CMake build type"
    )
    
    # Resource allocation
    parser.add_argument(
        "--cpus", 
        type=float,
        default=1.0,
        help="CPU allocation (Docker only)"
    )
    
    parser.add_argument(
        "--memory", 
        default="1G",
        help="Memory allocation (Docker only)"
    )
    
    # Scaling options
    parser.add_argument(
        "--replicas", 
        type=int,
        default=1,
        help="Number of replicas (Swarm/K8s only)"
    )
    
    # Network options
    parser.add_argument(
        "--port", 
        type=int,
        default=8080,
        help="External port to expose"
    )
    
    # Command to run in the container
    parser.add_argument(
        "--command",
        default="dashboard",
        help="Command to run"
    )
    
    # Environment file
    parser.add_argument(
        "--env-file",
        help="Path to environment file"
    )
    
    # Apply immediately
    parser.add_argument(
        "--apply", 
        action="store_true",
        help="Apply the deployment immediately"
    )
    
    # Output directory
    parser.add_argument(
        "--output-dir",
        default="deployment",
        help="Directory for generated files"
    )
    
    return parser.parse_args()

def check_docker_installed() -> bool:
    """Check if Docker is installed and running."""
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def build_docker_image(tag: str, build_type: str) -> bool:
    """Build the Docker image."""
    print(f"Building Docker image pipecat:{tag} with build type {build_type}...")
    
    try:
        result = subprocess.run(
            [
                "docker", "build", 
                "-t", f"pipecat:{tag}",
                "-f", "docker/Dockerfile",
                "--build-arg", f"BUILD_TYPE={build_type}",
                "."
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        print("✅ Docker image built successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Docker image: {e}")
        print(f"Error output: {e.stderr}")
        return False

def generate_docker_compose(args) -> Tuple[Path, Dict[str, Any]]:
    """Generate Docker Compose configuration."""
    output_dir = Path(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Create Docker Compose configuration
    compose_config = {
        "version": "3.8",
        "services": {
            "pipecat": {
                "image": f"pipecat:{args.tag}",
                "restart": "unless-stopped",
                "ports": [f"{args.port}:{args.port}"],
                "volumes": ["pipecat_cache:/app/cache"],
                "environment": [
                    "PIPECAT_CACHE_DIR=/app/cache",
                    "PIPECAT_ENV=production",
                    "PYTHONOPTIMIZE=2"
                ],
                "command": [args.command, "--host", "0.0.0.0", "--port", str(args.port)],
                "healthcheck": {
                    "test": f"curl --fail http://localhost:{args.port}/health || exit 1",
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            }
        },
        "volumes": {
            "pipecat_cache": {}
        }
    }
    
    # Add resource limits
    if args.cpus or args.memory:
        compose_config["services"]["pipecat"]["deploy"] = {
            "resources": {
                "limits": {}
            }
        }
        
        if args.cpus:
            compose_config["services"]["pipecat"]["deploy"]["resources"]["limits"]["cpus"] = str(args.cpus)
            
        if args.memory:
            compose_config["services"]["pipecat"]["deploy"]["resources"]["limits"]["memory"] = args.memory
    
    # Add environment file if provided
    if args.env_file:
        compose_config["services"]["pipecat"]["env_file"] = args.env_file
    
    # Add replicas for Swarm mode
    if args.mode == "swarm" and args.replicas > 1:
        if "deploy" not in compose_config["services"]["pipecat"]:
            compose_config["services"]["pipecat"]["deploy"] = {}
            
        compose_config["services"]["pipecat"]["deploy"]["replicas"] = args.replicas
    
    # Write Docker Compose file
    compose_file = output_dir / "docker-compose.yml"
    with open(compose_file, "w") as f:
        import yaml
        yaml.dump(compose_config, f, default_flow_style=False)
    
    print(f"✅ Generated Docker Compose file: {compose_file}")
    return compose_file, compose_config

def apply_docker_compose(compose_file: Path) -> bool:
    """Apply Docker Compose configuration."""
    try:
        print(f"Deploying with Docker Compose from {compose_file}...")
        result = subprocess.run(
            ["docker-compose", "-f", str(compose_file), "up", "-d"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        print("✅ Docker Compose deployment successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to deploy with Docker Compose: {e}")
        print(f"Error output: {e.stderr}")
        return False

def deploy_with_docker(args) -> bool:
    """Deploy using plain Docker."""
    try:
        container_name = f"pipecat-{args.command}"
        
        # Check if container exists and remove it
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if container_name in result.stdout:
            print(f"Removing existing container {container_name}...")
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        
        # Run the container
        cmd = [
            "docker", "run",
            "--name", container_name,
            "-d",
            "-p", f"{args.port}:{args.port}",
            "-v", "pipecat_cache:/app/cache",
            "-e", "PIPECAT_CACHE_DIR=/app/cache",
            "-e", "PIPECAT_ENV=production",
            "-e", "PYTHONOPTIMIZE=2",
        ]
        
        # Add resource limits
        if args.cpus:
            cmd.extend(["--cpus", str(args.cpus)])
            
        if args.memory:
            cmd.extend(["--memory", args.memory])
        
        # Add environment file if provided
        if args.env_file:
            cmd.extend(["--env-file", args.env_file])
        
        # Add image and command
        cmd.extend([
            f"pipecat:{args.tag}",
            args.command,
            "--host", "0.0.0.0",
            "--port", str(args.port)
        ])
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        
        print("✅ Docker deployment successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to deploy with Docker: {e}")
        print(f"Error output: {e.stderr}")
        return False

def deploy_with_swarm(args, compose_file: Path) -> bool:
    """Deploy to Docker Swarm."""
    try:
        # Check if Swarm is initialized
        result = subprocess.run(
            ["docker", "info", "--format", "{{.Swarm.LocalNodeState}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if "active" not in result.stdout:
            print("❌ Docker Swarm is not initialized. Run 'docker swarm init' first.")
            return False
        
        # Deploy the stack
        stack_name = f"pipecat-{args.command}"
        print(f"Deploying stack {stack_name} to Swarm...")
        
        result = subprocess.run(
            ["docker", "stack", "deploy", "--compose-file", str(compose_file), stack_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        
        print("✅ Swarm deployment successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to deploy to Swarm: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    args = parse_args()
    
    # Check if Docker is installed
    if not check_docker_installed():
        print("❌ Docker is not installed or running. Please install Docker and try again.")
        return 1
    
    # Import yaml here to avoid dependency issues
    try:
        import yaml
    except ImportError:
        print("❌ PyYAML is required for this script. Install it with: pip install PyYAML")
        return 1
    
    # Build the Docker image first
    if not build_docker_image(args.tag, args.build_type):
        return 1
    
    # Generate Docker Compose configuration
    if args.mode in ["compose", "swarm"]:
        compose_file, compose_config = generate_docker_compose(args)
    
    # Apply the configuration if requested
    if args.apply:
        if args.mode == "compose":
            if not apply_docker_compose(compose_file):
                return 1
        elif args.mode == "docker":
            if not deploy_with_docker(args):
                return 1
        elif args.mode == "swarm":
            if not deploy_with_swarm(args, compose_file):
                return 1
        elif args.mode == "kubernetes":
            print("❌ Kubernetes deployment not implemented yet.")
            return 1
    
    print("\n🎉 Deployment configuration complete!")
    print(f"Access the application at: http://localhost:{args.port}")
    
    if not args.apply:
        print("\nTo apply the deployment manually:")
        
        if args.mode == "compose":
            print(f"  docker-compose -f {compose_file} up -d")
        elif args.mode == "docker":
            print(f"  docker run -d -p {args.port}:{args.port} -v pipecat_cache:/app/cache pipecat:{args.tag} {args.command} --host 0.0.0.0 --port {args.port}")
        elif args.mode == "swarm":
            print(f"  docker stack deploy --compose-file {compose_file} pipecat-{args.command}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
