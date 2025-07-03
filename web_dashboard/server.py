"""
Flask Web Server for Dashboard

Provides the web server infrastructure for the interactive dashboard.
"""

import os
import threading
import time
from typing import Optional
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
import logging
from datetime import datetime

from .api import DashboardAPI
from container import initialize_telemetry_system


def create_app(config_name: str = 'development') -> Flask:
    """Flask application factory."""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Configuration
    if config_name == 'development':
        app.config['DEBUG'] = True
        app.config['TESTING'] = False
    elif config_name == 'production':
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
    elif config_name == 'testing':
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
    
    # Enable CORS for all routes
    CORS(app, origins=['http://localhost:*', 'http://127.0.0.1:*'])
    
    # Initialize telemetry container
    container = initialize_telemetry_system()
    app.container = container
    
    # Initialize API
    dashboard_api = DashboardAPI(container)
    dashboard_api.register_routes(app)
    
    # Dashboard route
    @app.route('/')
    def dashboard():
        """Main dashboard page."""
        return render_template('dashboard.html')
    
    # Health check route
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'agent-monitor-dashboard'
        }
    
    # Static files route
    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files."""
        return send_from_directory(app.static_folder, filename)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found', 'message': str(error)}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error', 'message': str(error)}, 500
    
    return app


class DashboardServer:
    """Web dashboard server lifecycle management."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5000, config: str = 'development'):
        self.host = host
        self.port = port
        self.config = config
        self.app = None
        self.server_thread = None
        self.is_running = False
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the web server."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('dashboard_server')
    
    def start(self) -> bool:
        """Start the web server in a separate thread."""
        if self.is_running:
            self.logger.warning("Server is already running")
            return False
        
        try:
            self.app = create_app(self.config)
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            
            # Wait a moment to ensure server starts
            time.sleep(1)
            
            self.is_running = True
            self.logger.info(f"Dashboard server started at http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
    
    def _run_server(self):
        """Run the Flask server."""
        try:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,  # Debug mode doesn't work well with threads
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            self.is_running = False
    
    def stop(self) -> bool:
        """Stop the web server."""
        if not self.is_running:
            self.logger.warning("Server is not running")
            return False
        
        try:
            self.is_running = False
            if self.server_thread and self.server_thread.is_alive():
                # Note: Flask doesn't have a clean shutdown method when running in threads
                # In production, we'd use a proper WSGI server like Gunicorn
                self.logger.info("Stopping dashboard server...")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop server: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart the web server."""
        self.logger.info("Restarting dashboard server...")
        if self.stop():
            time.sleep(2)  # Give time for cleanup
            return self.start()
        return False
    
    def get_status(self) -> dict:
        """Get server status information."""
        return {
            'running': self.is_running,
            'host': self.host,
            'port': self.port,
            'config': self.config,
            'url': f"http://{self.host}:{self.port}" if self.is_running else None
        }
    
    def get_url(self) -> Optional[str]:
        """Get the server URL if running."""
        if self.is_running:
            return f"http://{self.host}:{self.port}"
        return None 