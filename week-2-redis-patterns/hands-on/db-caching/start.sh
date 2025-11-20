#!/bin/bash

echo "🚀 Starting Blog API with Redis Caching..."
echo ""

# Build and start all services
echo "📦 Building and starting all services (Postgres + Redis + FastAPI)..."
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if services are running
if ! docker compose ps | grep -q "blog-api"; then
    echo "❌ API failed to start"
    docker compose logs app
    exit 1
fi

echo "✅ All services are running!"
echo ""
echo "📚 API docs:    http://localhost:8003/docs"
echo "🔍 View logs:   docker compose logs -f app"
echo "🛑 Stop:        ./stop.sh"
echo ""
echo "🧪 Run tests:   docker exec -it blog-api python test_performance.py"
echo ""

