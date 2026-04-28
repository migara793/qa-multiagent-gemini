#!/bin/bash

# QA Multi-Agent System - Setup Script
# Prepares the environment for first run

set -e  # Exit on error

echo "🚀 Setting up QA Multi-Agent System..."
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

command -v docker >/dev/null 2>&1 || {
    echo "❌ Docker not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
}

command -v docker compose >/dev/null 2>&1 || {
    echo "❌ Docker Compose not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
}

echo "✅ Docker installed: $(docker --version)"
echo "✅ Docker Compose installed: $(docker compose version)"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and add your API keys:"
    echo "   - GEMINI_API_KEY (required)"
    echo "   - GITHUB_TOKEN (optional)"
    echo ""
    echo "   Get Gemini API key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press ENTER after you've updated .env with your API keys..."
fi

# Validate GEMINI_API_KEY
source .env
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    echo "❌ GEMINI_API_KEY not set in .env file"
    echo "   Please add your Gemini API key to .env file"
    exit 1
fi

echo "✅ .env configuration found"
echo ""

# Create required directories
echo "📁 Creating directories..."
mkdir -p logs reports results
echo "✅ Directories created"
echo ""

# Pull base images
echo "🐳 Pulling Docker base images..."
docker pull postgres:15-alpine
docker pull redis:7-alpine
docker pull rabbitmq:3-management-alpine
echo "✅ Base images pulled"
echo ""

# Build custom images
echo "🔨 Building application images..."
docker compose build
echo "✅ Images built successfully"
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start the system:    ./scripts/start.sh"
echo "  2. Test the system:     ./scripts/test.sh"
echo "  3. View logs:           docker compose logs -f"
echo "  4. Stop the system:     ./scripts/stop.sh"
echo ""
