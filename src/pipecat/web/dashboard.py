"""
Dashboard implementation for Pipecat web interface.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
import asyncio
import json
import logging
from pathlib import Path
import os

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from ..pipeline import Pipeline
from ..monitoring.metrics import default_collector


@dataclass
class DashboardConfig:
    """Configuration for the Pipecat dashboard."""
    
    title: str = "Pipecat Dashboard"
    theme: str = "light"  # 'light' or 'dark'
    refresh_interval: int = 5  # seconds
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    enable_metrics: bool = True
    enable_logs: bool = True
    enable_pipeline_vis: bool = True
    widgets: List[str] = field(default_factory=lambda: ["metrics", "pipelines", "logs"])


class Dashboard:
    """Interactive web dashboard for monitoring Pipecat applications."""
    
    def __init__(self, 
                app: Optional[FastAPI] = None,
                config: Optional[DashboardConfig] = None,
                templates_dir: Optional[str] = None):
        """
        Initialize the dashboard.
        
        Args:
            app: FastAPI app to attach the dashboard to
            config: Dashboard configuration
            templates_dir: Directory containing custom templates
        """
        self.app = app or FastAPI(title="Pipecat Dashboard")
        self.config = config or DashboardConfig()
        self.logger = logging.getLogger("pipecat.web.dashboard")
        self.pipelines: Dict[str, Pipeline] = {}
        self._ws_connections: List[WebSocket] = []
        
        # Set up templates
        if templates_dir and os.path.exists(templates_dir):
            self.templates = Jinja2Templates(directory=templates_dir)
        else:
            # Use default templates
            template_path = Path(__file__).parent / "templates"
            if not template_path.exists():
                template_path.mkdir(parents=True)
                # Create default template file
                self._create_default_template(template_path)
            self.templates = Jinja2Templates(directory=str(template_path))
        
        # Set up static files
        static_path = Path(__file__).parent / "static"
        if not static_path.exists():
            static_path.mkdir(parents=True)
            # Create default CSS and JS files
            self._create_default_static_files(static_path)
        
        self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Set up routes
        self._setup_routes()
        
        # Start background task for metrics collection
        self._setup_background_tasks()
    
    def _setup_routes(self):
        """Set up the dashboard routes."""
        @self.app.get("/", response_class=HTMLResponse)
        async def get_dashboard(request: Request):
            """Return the main dashboard page."""
            return self.templates.TemplateResponse(
                "dashboard.html", 
                {
                    "request": request, 
                    "title": self.config.title,
                    "theme": self.config.theme,
                    "refresh_interval": self.config.refresh_interval,
                    "enable_metrics": self.config.enable_metrics,
                    "enable_logs": self.config.enable_logs,
                    "enable_pipeline_vis": self.config.enable_pipeline_vis,
                    "widgets": self.config.widgets
                }
            )
        
        @self.app.get("/api/dashboard/metrics")
        async def get_metrics():
            """Return the current metrics."""
            return default_collector.get_stats()
        
        @self.app.get("/api/dashboard/pipelines")
        async def get_pipelines():
            """Return information about registered pipelines."""
            return {
                name: {
                    "tasks": len(pipeline.tasks),
                    "status": pipeline.is_running(),
                    "metrics": pipeline.get_metrics() if hasattr(pipeline, "get_metrics") else {}
                }
                for name, pipeline in self.pipelines.items()
            }
        
        @self.app.websocket("/ws/dashboard")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self._ws_connections.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_json()
                    await self._handle_websocket_message(websocket, data)
            except WebSocketDisconnect:
                if websocket in self._ws_connections:
                    self._ws_connections.remove(websocket)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                if websocket in self._ws_connections:
                    self._ws_connections.remove(websocket)
    
    def _setup_background_tasks(self):
        """Set up background tasks."""
        @self.app.on_event("startup")
        async def startup_event():
            asyncio.create_task(self._metrics_publisher())
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            # Clean up tasks
            pass
    
    async def _metrics_publisher(self):
        """Periodically publish metrics to WebSocket clients."""
        while True:
            if self._ws_connections:
                metrics = default_collector.get_stats()
                
                # Send to all connected clients
                for ws in list(self._ws_connections):
                    try:
                        await ws.send_json({
                            "type": "metrics",
                            "data": metrics
                        })
                    except Exception as e:
                        self.logger.error(f"Error sending metrics: {e}")
                        if ws in self._ws_connections:
                            self._ws_connections.remove(ws)
            
            # Wait for next update
            await asyncio.sleep(self.config.refresh_interval)
    
    async def _handle_websocket_message(self, websocket: WebSocket, data: Dict[str, Any]):
        """Handle a WebSocket message."""
        if "type" not in data:
            await websocket.send_json({"error": "Missing message type"})
            return
        
        message_type = data["type"]
        
        if message_type == "request_metrics":
            # Send current metrics
            metrics = default_collector.get_stats()
            await websocket.send_json({
                "type": "metrics",
                "data": metrics
            })
        
        elif message_type == "request_pipelines":
            # Send pipeline information
            pipelines = {
                name: {
                    "tasks": len(pipeline.tasks),
                    "status": pipeline.is_running()
                }
                for name, pipeline in self.pipelines.items()
            }
            await websocket.send_json({
                "type": "pipelines",
                "data": pipelines
            })
        
        else:
            await websocket.send_json({"error": f"Unknown message type: {message_type}"})
    
    def register_pipeline(self, name: str, pipeline: Pipeline):
        """Register a pipeline with the dashboard."""
        self.pipelines[name] = pipeline
        
        # Register event handler for frames
        async def on_frame(frame):
            # Broadcast frame to connected WebSocket clients
            for ws in self._ws_connections:
                try:
                    await ws.send_json({
                        "type": "frame",
                        "pipeline": name,
                        "frame_type": frame.__class__.__name__,
                        "frame_data": frame.to_dict() if hasattr(frame, "to_dict") else str(frame)
                    })
                except Exception as e:
                    self.logger.error(f"Error sending frame: {e}")
        
        # Add observer to pipeline
        pipeline.add_observer(on_frame)
    
    def _create_default_template(self, template_path: Path):
        """Create a default dashboard template."""
        os.makedirs(template_path, exist_ok=True)
        
        dashboard_html = """
        {% extends "base.html" %}
        
        {% block content %}
        <div class="container">
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <h2>System Overview</h2>
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="stat-card">
                                        <h3>Pipelines</h3>
                                        <div class="stat-value" id="pipeline-count">0</div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="stat-card">
                                        <h3>Active Tasks</h3>
                                        <div class="stat-value" id="task-count">0</div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="stat-card">
                                        <h3>Frames Processed</h3>
                                        <div class="stat-value" id="frame-count">0</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            {% if "metrics" in widgets and enable_metrics %}
            <div class="row mb-4" id="metrics">
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
            {% endif %}
            
            {% if "pipelines" in widgets %}
            <div class="row mb-4" id="pipelines">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>Pipelines</h2>
                        </div>
                        <div class="card-body">
                            <div id="pipeline-list" class="pipeline-container">
                                <div class="alert alert-info">Loading pipelines...</div>
                            </div>
                            
                            {% if enable_pipeline_vis %}
                            <h3 class="mt-4">Pipeline Visualization</h3>
                            <div id="pipeline-vis" class="pipeline-vis-container">
                                <div class="alert alert-info">Select a pipeline to visualize.</div>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
            
            {% if "logs" in widgets and enable_logs %}
            <div class="row mb-4" id="logs">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>Logs</h2>
                        </div>
                        <div class="card-body">
                            <div class="log-container">
                                <pre id="log-output" class="log-output"></pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
        {% endblock %}
        """
        
        base_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ title }}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="{{ url_for('static', path='/dashboard.css') }}" rel="stylesheet">
            {% if theme == "dark" %}
            <link href="{{ url_for('static', path='/dark-theme.css') }}" rel="stylesheet">
            {% endif %}
            {% if custom_css %}
            <link href="{{ custom_css }}" rel="stylesheet">
            {% endif %}
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
                <div class="container-fluid">
                    <a class="navbar-brand" href="#">{{ title }}</a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav">
                            <li class="nav-item">
                                <a class="nav-link active" href="#">Dashboard</a>
                            </li>
                            {% if enable_metrics %}
                            <li class="nav-item">
                                <a class="nav-link" href="#metrics">Metrics</a>
                            </li>
                            {% endif %}
                            <li class="nav-item">
                                <a class="nav-link" href="#pipelines">Pipelines</a>
                            </li>
                            {% if enable_logs %}
                            <li class="nav-item">
                                <a class="nav-link" href="#logs">Logs</a>
                            </li>
                            {% endif %}
                        </ul>
                    </div>
                </div>
            </nav>
            
            {% block content %}{% endblock %}
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script src="{{ url_for('static', path='/dashboard.js') }}"></script>
            {% if custom_js %}
            <script src="{{ custom_js }}"></script>
            {% endif %}
            <script>
                // Initialize dashboard
                document.addEventListener('DOMContentLoaded', function() {
                    initDashboard({
                        refreshInterval: {{ refresh_interval }},
                        enableMetrics: {{ 'true' if enable_metrics else 'false' }},
                        enableLogs: {{ 'true' if enable_logs else 'false' }},
                        enablePipelineVis: {{ 'true' if enable_pipeline_vis else 'false' }}
                    });
                });
            </script>
        </body>
        </html>
        """
        
        with open(template_path / "dashboard.html", "w") as f:
            f.write(dashboard_html)
            
        with open(template_path / "base.html", "w") as f:
            f.write(base_html)
    
    def _create_default_static_files(self, static_path: Path):
        """Create default CSS and JS files for the dashboard."""
        os.makedirs(static_path, exist_ok=True)
        
        # Dashboard CSS
        dashboard_css = """
        .stat-card {
            text-align: center;
            padding: 15px;
            border-radius: 5px;
            background-color: #f8f9fa;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #0d6efd;
        }
        
        .log-container {
            max-height: 400px;
            overflow-y: auto;
            background-color: #f8f9fa;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }
        
        .log-output {
            padding: 10px;
            font-family: monospace;
            font-size: 0.9rem;
            margin-bottom: 0;
        }
        
        .pipeline-container {
            margin-bottom: 20px;
        }
        
        .pipeline-vis-container {
            height: 400px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            overflow: auto;
            padding: 10px;
            background-color: #f8f9fa;
        }
        
        .pipeline-card {
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .pipeline-card:hover {
            transform: translateX(5px);
        }
        
        .pipeline-card.active {
            border-color: #0d6efd;
            box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
        }
        """
        
        # Dark theme CSS
        dark_theme_css = """
        body {
            background-color: #121212;
            color: #e0e0e0;
        }
        
        .card {
            background-color: #1e1e1e;
            border-color: #333;
        }
        
        .card-header {
            background-color: #2d2d2d;
            border-color: #333;
        }
        
        .stat-card {
            background-color: #2d2d2d;
        }
        
        .log-container {
            background-color: #2d2d2d;
            border-color: #444;
        }
        
        .pipeline-vis-container {
            background-color: #2d2d2d;
            border-color: #444;
        }
        
        pre.log-output {
            color: #e0e0e0;
        }
        
        .alert-info {
            background-color: #2d3748;
            border-color: #4a5568;
            color: #e0e0e0;
        }
        """
        
        # Dashboard JavaScript
        dashboard_js = """
        // WebSocket connection
        let ws;
        
        // Charts
        let metricsChart;
        
        // Dashboard state
        const dashboardState = {
            selectedPipeline: null,
            metrics: {},
            pipelines: {},
            logs: []
        };
        
        function initDashboard(config) {
            // Connect to WebSocket
            connectWebSocket();
            
            // Set up UI updates
            setupPeriodicUpdates(config.refreshInterval);
            
            // Initialize metrics chart if enabled
            if (config.enableMetrics) {
                initMetricsChart();
            }
            
            // Load initial data
            loadPipelines();
            
            // Set up pipeline selection
            if (config.enablePipelineVis) {
                document.getElementById('pipeline-list').addEventListener('click', function(e) {
                    const pipelineCard = e.target.closest('.pipeline-card');
                    if (pipelineCard) {
                        const pipelineName = pipelineCard.dataset.name;
                        selectPipeline(pipelineName);
                    }
                });
            }
        }
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
            ws = new WebSocket(`${protocol}://${window.location.host}/ws/dashboard`);
            
            ws.onopen = function() {
                console.log('WebSocket connected');
                
                // Request initial data
                ws.send(JSON.stringify({ type: 'request_metrics' }));
                ws.send(JSON.stringify({ type: 'request_pipelines' }));
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'metrics') {
                    updateMetricsUI(data.data);
                } else if (data.type === 'pipelines') {
                    updatePipelinesUI(data.data);
                } else if (data.type === 'frame') {
                    handleFrame(data);
                } else if (data.type === 'log') {
                    appendLog(data.message, data.level);
                }
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected, reconnecting...');
                setTimeout(connectWebSocket, 2000);
            };
        }
        
        function setupPeriodicUpdates(interval) {
            // Update metrics periodically
            setInterval(function() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'request_metrics' }));
                }
            }, interval * 1000);
        }
        
        function loadPipelines() {
            fetch('/api/dashboard/pipelines')
                .then(response => response.json())
                .then(data => {
                    dashboardState.pipelines = data;
                    updatePipelinesUI(data);
                    
                    // Update overview stats
                    document.getElementById('pipeline-count').textContent = Object.keys(data).length;
                    
                    // Calculate total tasks
                    const taskCount = Object.values(data).reduce((sum, pipeline) => sum + pipeline.tasks, 0);
                    document.getElementById('task-count').textContent = taskCount;
                })
                .catch(error => console.error('Error loading pipelines:', error));
        }
        
        function updatePipelinesUI(pipelines) {
            const pipelineList = document.getElementById('pipeline-list');
            pipelineList.innerHTML = '';
            
            if (Object.keys(pipelines).length === 0) {
                pipelineList.innerHTML = '<div class="alert alert-info">No pipelines registered.</div>';
                return;
            }
            
            for (const [name, info] of Object.entries(pipelines)) {
                const card = document.createElement('div');
                card.className = `card pipeline-card ${dashboardState.selectedPipeline === name ? 'active' : ''}`;
                card.dataset.name = name;
                
                card.innerHTML = `
                    <div class="card-body">
                        <h5 class="card-title">${name}</h5>
                        <p>Tasks: ${info.tasks}</p>
                        <p>Status: <span class="badge ${info.status ? 'bg-success' : 'bg-secondary'}">
                            ${info.status ? 'Running' : 'Stopped'}
                        </span></p>
                    </div>
                `;
                
                pipelineList.appendChild(card);
            }
        }
        
        function initMetricsChart() {
            const ctx = document.getElementById('metrics-chart').getContext('2d');
            metricsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Metric Values',
                        data: [],
                        borderColor: 'rgba(54, 162, 235, 1)',
                        tension: 0.1,
                        fill: false
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
        
        function updateMetricsUI(metrics) {
            // Update charts if available
            if (metricsChart) {
                // Get the metrics we want to display
                const metricNames = Object.keys(metrics).slice(0, 10);  // Limit to first 10 metrics
                const metricValues = metricNames.map(name => {
                    const metric = metrics[name];
                    if (metric.type === 'counter') {
                        return metric.total;
                    } else {
                        return metric.latest;
                    }
                });
                
                metricsChart.data.labels = metricNames;
                metricsChart.data.datasets[0].data = metricValues;
                metricsChart.update();
            }
            
            // Store in state
            dashboardState.metrics = metrics;
        }
        
        function selectPipeline(name) {
            dashboardState.selectedPipeline = name;
            
            // Update UI to show the selected pipeline
            const cards = document.querySelectorAll('.pipeline-card');
            cards.forEach(card => {
                if (card.dataset.name === name) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
            });
            
            // Visualize the pipeline
            visualizePipeline(name);
        }
        
        function visualizePipeline(name) {
            const visContainer = document.getElementById('pipeline-vis');
            if (!visContainer) return;
            
            // Request pipeline structure (this would be implemented on the server)
            fetch(`/api/dashboard/pipelines/${name}/structure`)
                .then(response => response.json())
                .then(data => {
                    renderPipelineVisualization(visContainer, data);
                })
                .catch(error => {
                    console.error(`Error loading pipeline structure: ${error}`);
                    visContainer.innerHTML = `<div class="alert alert-danger">Error loading pipeline structure: ${error}</div>`;
                });
        }
        
        function renderPipelineVisualization(container, structure) {
            // This would use a visualization library like D3.js or mermaid.js
            // For now, just render a placeholder
            container.innerHTML = `<div class="alert alert-info">Pipeline visualization for ${structure.name} would be rendered here.</div>`;
        }
        
        function handleFrame(frameData) {
            console.log('Frame received:', frameData);
            
            // Update frame count
            const frameCount = document.getElementById('frame-count');
            frameCount.textContent = (parseInt(frameCount.textContent) || 0) + 1;
            
            // If the frame is a log message, append to logs
            if (frameData.frame_type === 'LogFrame') {
                appendLog(frameData.frame_data.message, frameData.frame_data.level);
            }
        }
        
        function appendLog(message, level) {
            const logOutput = document.getElementById('log-output');
            if (!logOutput) return;
            
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = `[${timestamp}] [${level}] ${message}\\n`;
            
            // Add to logs
            dashboardState.logs.push(logEntry);
            
            // Limit the number of logs to keep in memory
            if (dashboardState.logs.length > 100) {
                dashboardState.logs.shift();
            }
            
            // Update UI
            logOutput.textContent = dashboardState.logs.join('');
            
            // Scroll to bottom
            logOutput.scrollTop = logOutput.scrollHeight;
        }
        """
        
        with open(static_path / "dashboard.css", "w") as f:
            f.write(dashboard_css)
            
        with open(static_path / "dark-theme.css", "w") as f:
            f.write(dark_theme_css)
            
        with open(static_path / "dashboard.js", "w") as f:
            f.write(dashboard_js)
