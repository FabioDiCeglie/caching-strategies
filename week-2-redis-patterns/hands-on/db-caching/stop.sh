#!/bin/bash

echo "🛑 Stopping Blog API services..."
echo ""

# Stop Docker services
echo "📦 Stopping Docker services..."
docker compose down

echo ""
echo "✅ All services stopped"
echo ""
echo "To clean all data (including database), run:"
echo "  docker compose down -v"

