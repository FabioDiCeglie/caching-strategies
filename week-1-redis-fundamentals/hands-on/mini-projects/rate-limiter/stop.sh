#!/bin/bash

echo "🛑 Stopping Rate Limiter services..."
echo ""

# Stop Docker services and remove volumes
echo "📦 Stopping Docker services and cleaning all data..."
docker compose down -v

echo ""
echo "✅ All services stopped and data cleaned"

