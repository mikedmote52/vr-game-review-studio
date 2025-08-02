#!/bin/bash
echo "Starting VR Game Review Studio Web Server..."
cd web_interface
export FLASK_HOST=0.0.0.0
export FLASK_PORT=${PORT:-10000}
export FLASK_DEBUG=False
echo "Running on port: $FLASK_PORT"
python app.py