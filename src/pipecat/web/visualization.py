"""
Pipeline visualization utilities for Pipecat web interfaces.
"""
import json
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx
from pathlib import Path

from ..pipeline import Pipeline


class PipelineVisualizer:
    """Class for generating visual representations of Pipecat pipelines."""
    
    def __init__(self, include_details: bool = True):
        """
        Initialize the pipeline visualizer.
        
        Args:
            include_details: Whether to include detailed information about each task
        """
        self.include_details = include_details
    
    def to_graph(self, pipeline: Pipeline) -> nx.DiGraph:
        """
        Convert a pipeline to a NetworkX directed graph.
        
        Args:
            pipeline: The pipeline to visualize
            
        Returns:
            A NetworkX DiGraph representation of the pipeline
        """
        graph = nx.DiGraph()
        
        # Add nodes (tasks)
        for i, task in enumerate(pipeline.tasks):
            task_name = getattr(task, "name", f"Task {i}")
            task_type = task.__class__.__name__
            
            # Add node with attributes
            graph.add_node(
                i, 
                name=task_name,
                type=task_type,
                module=task.__class__.__module__
            )
            
            # Add additional details if requested
            if self.include_details:
                graph.nodes[i]["details"] = self._get_task_details(task)
        
        # Add edges (connections between tasks)
        for i in range(len(pipeline.tasks) - 1):
            graph.add_edge(i, i + 1)
        
        return graph
    
    def to_json(self, pipeline: Pipeline) -> Dict[str, Any]:
        """
        Convert a pipeline to a JSON-serializable dictionary.
        
        Args:
            pipeline: The pipeline to visualize
            
        Returns:
            A dictionary representing the pipeline structure
        """
        graph = self.to_graph(pipeline)
        
        # Convert graph to dictionary
        result = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes
        for node_id, attrs in graph.nodes(data=True):
            result["nodes"].append({
                "id": node_id,
                **attrs
            })
        
        # Add edges
        for source, target in graph.edges():
            result["edges"].append({
                "source": source,
                "target": target
            })
        
        return result
    
    def to_mermaid(self, pipeline: Pipeline) -> str:
        """
        Convert a pipeline to a Mermaid.js flowchart string.
        
        Args:
            pipeline: The pipeline to visualize
            
        Returns:
            A Mermaid.js flowchart string
        """
        graph = self.to_graph(pipeline)
        
        # Start flowchart
        mermaid = ["flowchart TD"]
        
        # Add nodes
        for node_id, attrs in graph.nodes(data=True):
            node_name = attrs.get("name", f"Task {node_id}")
            node_type = attrs.get("type", "Unknown")
            
            # Create node ID and label
            node_id_str = f"node{node_id}"
            label = f"{node_name}<br>{node_type}"
            
            # Add node
            mermaid.append(f"    {node_id_str}[\"{label}\"]")
        
        # Add edges
        for source, target in graph.edges():
            source_id = f"node{source}"
            target_id = f"node{target}"
            mermaid.append(f"    {source_id} --> {target_id}")
        
        return "\n".join(mermaid)
    
    def to_html(self, pipeline: Pipeline, include_js: bool = True) -> str:
        """
        Convert a pipeline to an HTML visualization.
        
        Args:
            pipeline: The pipeline to visualize
            include_js: Whether to include JavaScript libraries
            
        Returns:
            HTML string with the visualization
        """
        pipeline_json = json.dumps(self.to_json(pipeline))
        
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <title>Pipeline Visualization</title>"
        ]
        
        if include_js:
            html.extend([
                "    <script src=\"https://d3js.org/d3.v7.min.js\"></script>",
                "    <style>",
                "        .node { cursor: pointer; }",
                "        .node circle { fill: #fff; stroke: steelblue; stroke-width: 3px; }",
                "        .node text { font: 12px sans-serif; }",
                "        .link { fill: none; stroke: #ccc; stroke-width: 2px; }",
                "    </style>"
            ])
        
        html.extend([
            "</head>",
            "<body>",
            "    <div id=\"pipeline-visualization\"></div>",
            f"    <script>const pipelineData = {pipeline_json};</script>"
        ])
        
        if include_js:
            html.extend([
                "    <script>",
                "        // D3.js visualization code",
                "        const width = 960;",
                "        const height = 600;",
                "",
                "        const svg = d3.select('#pipeline-visualization')",
                "            .append('svg')",
                "            .attr('width', width)",
                "            .attr('height', height);",
                "",
                "        const g = svg.append('g');",
                "",
                "        // Create a simulation for the graph",
                "        const simulation = d3.forceSimulation()",
                "            .force('link', d3.forceLink().id(d => d.id).distance(150))",
                "            .force('charge', d3.forceManyBody().strength(-300))",
                "            .force('center', d3.forceCenter(width / 2, height / 2));",
                "",
                "        // Add links",
                "        const link = g.append('g')",
                "            .attr('class', 'links')",
                "            .selectAll('line')",
                "            .data(pipelineData.edges)",
                "            .enter().append('line')",
                "            .attr('class', 'link');",
                "",
                "        // Add nodes",
                "        const node = g.append('g')",
                "            .attr('class', 'nodes')",
                "            .selectAll('.node')",
                "            .data(pipelineData.nodes)",
                "            .enter().append('g')",
                "            .attr('class', 'node');",
                "",
                "        // Add circles to nodes",
                "        node.append('circle')",
                "            .attr('r', 30);",
                "",
                "        // Add labels to nodes",
                "        node.append('text')",
                "            .attr('dy', '.35em')",
                "            .attr('text-anchor', 'middle')",
                "            .text(d => d.name);",
                "",
                "        // Update node and link positions on simulation tick",
                "        simulation.nodes(pipelineData.nodes).on('tick', () => {",
                "            link",
                "                .attr('x1', d => d.source.x)",
                "                .attr('y1', d => d.source.y)",
                "                .attr('x2', d => d.target.x)",
                "                .attr('y2', d => d.target.y);",
                "",
                "            node.attr('transform', d => `translate(${d.x},${d.y})`);",
                "        });",
                "",
                "        // Apply link force",
                "        simulation.force('link').links(pipelineData.edges);",
                "    </script>"
            ])
        
        html.extend([
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html)
    
    def _get_task_details(self, task: Any) -> Dict[str, Any]:
        """Extract relevant details from a task object."""
        details = {}
        
        # Get basic information
        for attr in dir(task):
            # Skip private attributes and methods
            if attr.startswith("_") or callable(getattr(task, attr)):
                continue
                
            try:
                value = getattr(task, attr)
                
                # Skip complex objects
                if not isinstance(value, (str, int, float, bool, list, dict, tuple, set)):
                    continue
                    
                details[attr] = value
            except Exception:
                pass
        
        return details
    
    def save_visualization(self, pipeline: Pipeline, output_path: str, format: str = "html") -> Path:
        """
        Save a visualization of the pipeline to a file.
        
        Args:
            pipeline: The pipeline to visualize
            output_path: Path to save the visualization
            format: Format of the visualization (html, mermaid, json, svg)
            
        Returns:
            Path to the saved file
        """
        path = Path(output_path)
        os.makedirs(path.parent, exist_ok=True)
        
        if format.lower() == "html":
            with open(path, "w") as f:
                f.write(self.to_html(pipeline))
        elif format.lower() == "mermaid":
            with open(path, "w") as f:
                f.write(self.to_mermaid(pipeline))
        elif format.lower() == "json":
            with open(path, "w") as f:
                json.dump(self.to_json(pipeline), f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return path
