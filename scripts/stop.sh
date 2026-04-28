#!/bin/bash

# QA Multi-Agent System - Stop Script

echo "🛑 Stopping QA Multi-Agent System..."
echo ""

docker compose down

echo ""
echo "✅ System stopped"
echo ""
echo "To remove all data (volumes):"
echo "   docker compose down -v"
echo ""
