"""
Web server for Pipecat applications.
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..pipeline import Pipeline
from ..frames import Frame, TextFrame
from ..monitoring.metrics import default_collector


class WebServer:
    """Web server for Pipecat applications."""
    
    def __init__(self, 
                title: str = "Pipecat Server", 
                static_dir: Optional[str] = None):
        """
        Initialize the web server.
        
        Args:
            title: Title for the web server
            static_dir: Directory containing static files (HTML, CSS, JS)
        """
        self.app = FastAPI(title=title)
        self.logger = logging.getLogger("pipecat.web.server")
        self.pipelines: Dict[str, Pipeline] = {}
        self._connections: Dict[str, List[WebSocket]] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Set up static file serving if directory is provided
        if static_dir:
            static_path = Path(static_dir)
            if static_path.exists() and static_path.is_dir():
                self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        # Set up routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up the API routes."""
        @self.app.get("/")
        async def get_index():
            """Return the index page."""
            return HTMLResponse(self._get_index_html())
        
        @self.app.get("/api/pipelines")
        async def get_pipelines():
            """Return information about registered pipelines."""
            return {
                name: {
                    "tasks": len(pipeline.tasks),
                    "status": pipeline.is_running(),
                }
                for name, pipeline in self.pipelines.items()
            }
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Return metrics from the metrics collector."""
            return default_collector.get_stats()
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            
            # Add to general connections
            self._add_connection("all", websocket)
            
            try:
                while True:
                    data = await websocket.receive_json()
                    await self._handle_websocket_message(websocket, data)
            except WebSocketDisconnect:
                # Remove connection
                self._remove_connection("all", websocket)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                # Remove connection
                self._remove_connection("all", websocket)
    
    def _get_index_html(self) -> str:
        """Return the HTML for the index page."""
        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Pipecat Admin</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    body {{ padding: 20px; }}
                    .pipeline-card {{ margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Pipecat Admin</h1>
                    <div class="row" id="pipelines">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header">
                                    <h2>Pipelines</h2>
                                </div>
                                <div class="card-body" id="pipeline-list">
                                    <p>Loading pipelines...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row mt-4">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header">
                                    <h2>Metrics</h2>
                                </div>
                                <div class="card-body">
                                    <canvas id="metrics-chart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    // Connect to WebSocket
                    const ws = new WebSocket(`${{window.location.protocol === 'https:' ? 'wss' : 'ws'}}://${{window.location.host}}/ws`);
                    
                    // Load pipeline data
                    fetch('/api/pipelines')
                        .then(response => response.json())
                        .then(data => {
                            const pipelineList = document.getElementById('pipeline-list');
                            pipelineList.innerHTML = '';
                            
                            if (Object.keys(data).length === 0) {
                                pipelineList.innerHTML = '<p>No pipelines registered.</p>';
                                return;
                            }
                            
                            for (const [name, info] of Object.entries(data)) {
                                const card = document.createElement('div');
                                card.className = 'card pipeline-card';
                                card.innerHTML = `
                                    <div class="card-body">
                                        <h5 class="card-title">${{name}}</h5>
                                        <p>Tasks: ${{info.tasks}}</p>
                                        <p>Status: <span class="badge ${{info.status ? 'bg-success' : 'bg-secondary'}}">
                                            ${{info.status ? 'Running' : 'Stopped'}}
                                        </span></p>
                                    </div>
                                `;
                                pipelineList.appendChild(card);
                            }
                        })
                        .catch(error => {
                            console.error('Error loading pipelines:', error);
                            document.getElementById('pipeline-list').innerHTML = 
                                '<div class="alert alert-danger">Error loading pipeline data.</div>';
                        });
                    
                    // Load metrics data
                    let metricsChart;
                    
                    function updateMetrics() {
                        fetch('/api/metrics')
                            .then(response => response.json())
                            .then(data => {
                                const labels = Object.keys(data);
                                const values = labels.map(label => {
                                    if (data[label].type === 'counter') {
                                        return data[label].total;
                                    } else {
                                        return data[label].latest;
                                    }
                                });
                                
                                if (metricsChart) {
                                    metricsChart.data.labels = labels;
                                    metricsChart.data.datasets[0].data = values;
                                    metricsChart.update();
                                } else {
                                    const ctx = document.getElementById('metrics-chart').getContext('2d');
                                    metricsChart = new Chart(ctx, {
                                        type: 'bar',
                                        data: {
                                            labels: labels,
                                            datasets: [{
                                                label: 'Metric Values',
                                                data: values,
                                                backgroundColor: 'rgba(54, 162, 235, 0.5)'
                                            }]
                                        },
                                        options: {
                                            responsive: true,
                                            scales: {
                                                y: {
                                                    beginAtZero: true
                                                }
                                            }
                                        }
                                    });
                                }
                            })
                            .catch(error => {
                                console.error('Error loading metrics:', error);
                            });
                    }
                    
                    // Initial metrics update
                    updateMetrics();
                    
                    // Update metrics every 5 seconds
                    setInterval(updateMetrics, 5000);
                    
                    // WebSocket message handling
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        console.log('Received:', data);
                    };
                    
                    ws.onclose = function(event) {
                        console.log('Connection closed');
                    };
                    
                    ws.onerror = function(error) {
                        console.error('WebSocket error:', error);
                    };
                </script>
            </body>
        </html>
        """
    
    def _add_connection(self, group: str, websocket: WebSocket):
        """Add a WebSocket connection to a group."""
        if group not in self._connections:
            self._connections[group] = []
        self._connections[group].append(websocket)
    
    def _remove_connection(self, group: str, websocket: WebSocket):
        """Remove a WebSocket connection from a group."""
        if group in self._connections:
            if websocket in self._connections[group]:
                self._connections[group].remove(websocket)
    
    async def _handle_websocket_message(self, websocket: WebSocket, data: Dict[str, Any]):
        """Handle a message received over WebSocket."""
        if "type" not in data:
            await websocket.send_json({"error": "Missing message type"})
            return
        
        message_type = data["type"]
        
        if message_type == "subscribe":
            # Subscribe to pipeline events
            if "pipeline" in data and data["pipeline"] in self.pipelines:
                self._add_connection(data["pipeline"], websocket)
                await websocket.send_json({"status": "subscribed", "pipeline": data["pipeline"]})
            else:
                await websocket.send_json({"error": "Invalid pipeline"})
        
        elif message_type == "text":
            # Send a text message to a pipeline
            if "pipeline" in data and data["pipeline"] in self.pipelines:
                if "text" in data:
                    pipeline = self.pipelines[data["pipeline"]]
                    # Create and send a text frame
                    frame = TextFrame(text=data["text"], source="web")
                    asyncio.create_task(pipeline.process_async(frame))
                    await websocket.send_json({"status": "processing"})
                else:
                    await websocket.send_json({"error": "Missing text"})
            else:
                await websocket.send_json({"error": "Invalid pipeline"})
        
        else:
            await websocket.send_json({"error": f"Unknown message type: {message_type}"})
    
    def register_pipeline(self, name: str, pipeline: Pipeline):
        """Register a pipeline with the server."""
        self.pipelines[name] = pipeline
        
        # Set up event handler to forward frames to WebSocket clients
        async def on_frame(frame: Frame):
            if name in self._connections:
                for ws in self._connections[name]:
                    try:
                        await ws.send_json({
                            "type": "frame",
                            "pipeline": name,
                            "frame": {
                                "type": frame.__class__.__name__,
                                "data": frame.to_dict()
                            }
                        })
                    except Exception as e:
                        self.logger.error(f"Error sending frame to WebSocket: {e}")
        
        # Register the event handler
        pipeline.add_observer(on_frame)
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler for a specific event type."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the web server."""
        import uvicorn
        
        config = uvicorn.Config(app=self.app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()
