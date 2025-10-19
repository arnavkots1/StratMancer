@echo off
REM Production deployment script for StratMancer (Windows)

echo 🚀 StratMancer Production Deployment
echo ==================================

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.example .env
    echo ⚠️  Please edit .env file with your production settings before continuing.
    echo    Required: API_KEY, CORS_ORIGINS
    pause
)

REM Stop any existing containers
echo 🛑 Stopping existing containers...
docker-compose down --remove-orphans

REM Build and start services
echo 🔨 Building and starting services...
docker-compose up --build -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check if services are running
echo 🔍 Checking service status...
docker-compose ps

REM Run health checks
echo 🏥 Running health checks...

REM Check API health
echo Testing API health...
curl -f http://localhost:8000/healthz >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ API is healthy
) else (
    echo ❌ API health check failed
    pause
    exit /b 1
)

REM Check web interface
echo Testing web interface...
curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Web interface is accessible
) else (
    echo ❌ Web interface check failed
    pause
    exit /b 1
)

REM Check metrics endpoint
echo Testing metrics endpoint...
curl -f http://localhost:8000/metrics >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Metrics endpoint is accessible
) else (
    echo ❌ Metrics endpoint check failed
    pause
    exit /b 1
)

REM Run comprehensive validation
echo 🧪 Running comprehensive validation...
python validate_production.py

if %errorlevel% equ 0 (
    echo.
    echo 🎉 StratMancer is successfully deployed!
    echo.
    echo 📊 Access Points:
    echo    API: http://localhost:8000
    echo    Web: http://localhost:3000
    echo    Docs: http://localhost:8000/docs
    echo    Metrics: http://localhost:8000/metrics
    echo    Health: http://localhost:8000/healthz
    echo.
    echo 📝 Next Steps:
    echo    1. Configure your reverse proxy (nginx/traefik) for HTTPS
    echo    2. Set up monitoring (Prometheus/Grafana)
    echo    3. Configure log aggregation
    echo    4. Set up automated backups
    echo.
    echo 🔧 Management Commands:
    echo    View logs: docker-compose logs -f
    echo    Stop services: docker-compose down
    echo    Restart services: docker-compose restart
    echo    Update services: docker-compose pull ^&^& docker-compose up -d
) else (
    echo ❌ Validation failed. Please check the logs and fix issues.
    pause
    exit /b 1
)

pause
