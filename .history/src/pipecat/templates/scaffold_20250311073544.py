"""
Project scaffolding utilities for creating new Pipecat projects.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import jinja2


class TemplateError(Exception):
    """Exception raised for template-related errors."""
    pass


def available_templates() -> Dict[str, Dict[str, str]]:
    """
    Get available project templates.
    
    Returns:
        Dictionary of template names mapped to their descriptions and metadata
    """
    templates_dir = Path(__file__).parent / "project_templates"
    templates = {}
    
    for template_dir in templates_dir.iterdir():
        if not template_dir.is_dir():
            continue
        
        # Look for template metadata
        metadata_path = template_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)
        else:
            metadata = {
                "description": f"Project template: {template_dir.name}",
                "version": "0.1.0"
            }
        
        templates[template_dir.name] = metadata
    
    return templates


def create_project(template_name: str, 
                  output_dir: str, 
                  project_name: str,
                  author: str = "",
                  variables: Optional[Dict[str, Any]] = None) -> Path:
    """
    Create a new project from a template.
    
    Args:
        template_name: Name of the template to use
        output_dir: Directory where project will be created
        project_name: Name of the project
        author: Project author name
        variables: Additional variables for template rendering
        
    Returns:
        Path to the created project
    
    Raises:
        TemplateError: If template doesn't exist or there's an error creating the project
    """
    templates_dir = Path(__file__).parent / "project_templates"
    template_dir = templates_dir / template_name
    
    if not template_dir.exists() or not template_dir.is_dir():
        raise TemplateError(f"Template '{template_name}' not found")
    
    # Create the output directory if it doesn't exist
    output_path = Path(output_dir) / project_name
    os.makedirs(output_path, exist_ok=True)
    
    # Create the context for template rendering
    context = {
        "project_name": project_name,
        "author": author,
        "project_slug": project_name.lower().replace(" ", "_").replace("-", "_"),
    }
    
    # Add custom variables to context
    if variables:
        context.update(variables)
    
    # Set up Jinja environment
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        keep_trailing_newline=True,
        autoescape=False,
    )
    
    # Process all files in the template directory
    for template_file in _list_template_files(template_dir):
        relative_path = template_file.relative_to(template_dir)
        
        # Skip special files
        if str(relative_path) == "metadata.json":
            continue
        
        # Path in output directory, replacing template variables in filename
        output_file_path_str = str(relative_path)
        for key, value in context.items():
            if isinstance(value, str):
                output_file_path_str = output_file_path_str.replace(
                    f"__{key}__", value
                )
        
        output_file_path = output_path / output_file_path_str
        
        # Create parent directories if they don't exist
        os.makedirs(output_file_path.parent, exist_ok=True)
        
        # Process the template file if it has a .j2 extension
        if template_file.name.endswith(".j2"):
            # Remove .j2 extension from output file
            output_file_path = output_file_path.with_name(
                output_file_path.name[:-3]
            )
            
            # Render the template
            template = env.get_template(str(relative_path))
            rendered_content = template.render(**context)
            
            # Write the rendered content to the output file
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(rendered_content)
        else:
            # Copy the file directly
            shutil.copy2(template_file, output_file_path)
    
    print(f"Project '{project_name}' created at {output_path}")
    return output_path


def _list_template_files(directory: Path) -> List[Path]:
    """Recursively list all files in a directory."""
    files = []
    for path in directory.glob("**/*"):
        if path.is_file():
            files.append(path)
    return files
