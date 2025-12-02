#!/bin/bash

echo "🚀 Starting HTTP Caching Headers Demo..."
echo "=========================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo ""
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Build and start containers
docker compose up --build -d

echo ""
echo "✅ Server is running!"
echo ""
echo "📱 Open in browser:"
echo "   http://localhost:8000"
echo ""
echo "🔍 View logs:"
echo "   docker compose logs -f"
echo ""
echo "🛑 To stop:"
echo "   ./stop.sh"
echo ""
