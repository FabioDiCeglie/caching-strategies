#!/bin/bash

echo "🚀 Starting Distributed Locks Demo..."
echo ""

# Build and start all services
echo "📦 Building and starting all services (Postgres + Redis + FastAPI)..."
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if services are running
if ! docker compose ps | grep -q "booking-api"; then
    echo "❌ API failed to start"
    docker compose logs app
    exit 1
fi

echo "✅ All services are running!"
echo ""
echo "📚 API docs:    http://localhost:8005/docs"
echo "🔍 View logs:   docker compose logs -f app"
echo "🛑 Stop:        ./stop.sh"
echo ""
echo "Run tests with: docker exec -it booking-api python test_concurrent.py"
echo ""

