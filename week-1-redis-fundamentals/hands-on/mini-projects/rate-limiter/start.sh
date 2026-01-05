#!/bin/bash

echo "🚀 Starting Rate Limiter Demo..."
echo ""

# Build and start all services
echo "📦 Building and starting services (Redis + FastAPI)..."
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 3

# Check if services are running
if ! docker compose ps | grep -q "rate-limiter-api"; then
    echo "❌ API failed to start"
    docker compose logs app
    exit 1
fi

echo "✅ All services are running!"
echo ""
echo "📚 API docs:    http://localhost:8001/docs"
echo "🔍 View logs:   docker compose logs -f app"
echo "🛑 Stop:        ./stop.sh"
echo ""

