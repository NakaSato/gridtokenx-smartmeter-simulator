#!/bin/bash
# Quick script to build and run the Docker container

echo "🔨 Building Docker image..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "🚀 Starting container..."
    docker-compose up -d
    
    echo ""
    echo "📊 Container status:"
    docker-compose ps
    
    echo ""
    echo "🌐 Application should be available at: http://localhost:8000"
    echo ""
    echo "📝 Useful commands:"
    echo "  View logs:        docker-compose logs -f"
    echo "  Stop container:   docker-compose down"
    echo "  Restart:          docker-compose restart"
    echo "  View health:      curl http://localhost:8000/health"
else
    echo "❌ Build failed!"
    exit 1
fi
