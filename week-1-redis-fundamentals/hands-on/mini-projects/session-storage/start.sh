#!/bin/bash

echo "🚀 Starting Session Storage Demo..."
echo ""

# Build and start all services
echo "📦 Building and starting services (Redis + FastAPI)..."
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 3

# Check if services are running
if ! docker compose ps | grep -q "session-storage-api"; then
    echo "❌ API failed to start"
    docker compose logs app
    exit 1
fi

echo "✅ All services are running!"
echo ""
echo "📚 API docs:    http://localhost:8002/docs"
echo "🔍 View logs:   docker compose logs -f app"
echo "🛑 Stop:        ./stop.sh"
echo ""

