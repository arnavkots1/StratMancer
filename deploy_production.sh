#!/bin/bash
# Production deployment script for StratMancer

set -e  # Exit on any error

echo "🚀 StratMancer Production Deployment"
echo "=================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your production settings before continuing."
    echo "   Required: API_KEY, CORS_ORIGINS"
    read -p "Press Enter when you've updated .env file..."
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Run health checks
echo "🏥 Running health checks..."

# Check API health
echo "Testing API health..."
if curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ API is healthy"
else
    echo "❌ API health check failed"
    exit 1
fi

# Check web interface
echo "Testing web interface..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Web interface is accessible"
else
    echo "❌ Web interface check failed"
    exit 1
fi

# Check metrics endpoint
echo "Testing metrics endpoint..."
if curl -f http://localhost:8000/metrics > /dev/null 2>&1; then
    echo "✅ Metrics endpoint is accessible"
else
    echo "❌ Metrics endpoint check failed"
    exit 1
fi

# Run comprehensive validation
echo "🧪 Running comprehensive validation..."
python validate_production.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 StratMancer is successfully deployed!"
    echo ""
    echo "📊 Access Points:"
    echo "   API: http://localhost:8000"
    echo "   Web: http://localhost:3000"
    echo "   Docs: http://localhost:8000/docs"
    echo "   Metrics: http://localhost:8000/metrics"
    echo "   Health: http://localhost:8000/healthz"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Configure your reverse proxy (nginx/traefik) for HTTPS"
    echo "   2. Set up monitoring (Prometheus/Grafana)"
    echo "   3. Configure log aggregation"
    echo "   4. Set up automated backups"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop services: docker-compose down"
    echo "   Restart services: docker-compose restart"
    echo "   Update services: docker-compose pull && docker-compose up -d"
else
    echo "❌ Validation failed. Please check the logs and fix issues."
    exit 1
fi
