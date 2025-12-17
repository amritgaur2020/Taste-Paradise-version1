#!/bin/bash
set -e
echo "Building frontend application..."
cd frontend
echo "Installing dependencies..."
npm install
echo "Building app..."
npm run build
echo "Build completed successfully!"
