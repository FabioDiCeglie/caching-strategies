#!/bin/bash

echo "🛑 Stopping Thundering Herd Demo..."
echo ""

# Stop Docker services and remove volumes
echo "📦 Stopping Docker services and cleaning all data..."
docker compose down -v

echo ""
echo "✅ All services stopped and data cleaned"
