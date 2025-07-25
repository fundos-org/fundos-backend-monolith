#!/bin/bash

# Check if redis-shared container is running
if docker ps --filter "name=redis-shared" --format '{{.Names}}' | grep -q "redis-shared"; then
  echo "✅ Redis container is running"
  docker compose -f docker-compose.yml up -d --build
else
  echo "❗️ Redis container not running. Please start it first."
  exit 1
fi