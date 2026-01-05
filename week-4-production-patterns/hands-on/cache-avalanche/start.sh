#!/bin/bash

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "🚀 Starting Cache Avalanche Demo..."
echo ""

# Build and start all services
echo "📦 Building and starting services (Redis + FastAPI)..."
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 3

# Check if services are running
if ! docker compose ps | grep -q "cache-avalanche"; then
    echo "❌ API failed to start"
    docker compose logs app
    exit 1
fi

echo "✅ All services are running!"
echo ""
echo "🌐 Demo UI:     http://localhost:8006"
echo "🔍 View logs:   docker compose logs -f app"
echo "🛑 Stop:        ./stop.sh"
echo ""
echo "🧪 Run test:    docker exec -it cache-avalanche-api python test_avalanche.py"
echo ""

