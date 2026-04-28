#!/bin/bash

# QA Multi-Agent System - Start Script
# Starts all services in the correct order

set -e

echo "🚀 Starting QA Multi-Agent System..."
echo ""

# Start infrastructure first (PostgreSQL, Redis, RabbitMQ)
echo "📦 Starting infrastructure services..."
docker compose up -d postgres redis rabbitmq

echo "⏳ Waiting for infrastructure to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."

# Wait for PostgreSQL
until docker compose exec postgres pg_isready -U qauser >/dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL ready"

# Wait for Redis
until docker compose exec redis redis-cli -a ${REDIS_PASSWORD:-redispassword123} ping >/dev/null 2>&1; do
    echo "   Waiting for Redis..."
    sleep 2
done
echo "✅ Redis ready"

echo ""

# Start MCP servers
echo "🔌 Starting MCP servers..."
docker compose up -d test-strategy-server

sleep 5
echo "✅ MCP servers started"
echo ""

# Start agents
echo "🤖 Starting test agents..."
docker compose up -d unit-test-agent

sleep 3
echo "✅ Agents started"
echo ""

# Start runner (main service)
echo "🎯 Starting runner service..."
docker compose up -d runner

echo "⏳ Waiting for runner to be ready..."
sleep 10

# Check if runner is healthy
until curl -s http://localhost:8000/health >/dev/null 2>&1; do
    echo "   Waiting for runner..."
    sleep 3
done

echo ""
echo "✅ QA Multi-Agent System is running!"
echo ""
echo "📊 Service URLs:"
echo "   Runner API:       http://localhost:8000"
echo "   API Docs:         http://localhost:8000/docs"
echo "   RabbitMQ:         http://localhost:15672 (guest/guest)"
echo ""
echo "📝 Useful commands:"
echo "   View logs:        docker compose logs -f"
echo "   View runner logs: docker compose logs -f runner"
echo "   Test system:      ./scripts/test.sh"
echo "   Stop system:      ./scripts/stop.sh"
echo ""
