#!/bin/bash

# 🚀 Ollama API Startup Script
# Handles both local testing and Docker container scenarios

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if Ollama is running
check_ollama() {
    local url=$1
    if curl -s "$url/api/tags" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for Ollama to be ready
wait_for_ollama() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    print_info "Waiting for Ollama to be ready at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if check_ollama "$url"; then
            print_success "Ollama is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Ollama failed to start after $max_attempts attempts"
    return 1
}

# Function to ensure model is available
ensure_model() {
    local url=$1
    local model=$2
    
    print_info "Checking if model '$model' is available..."
    
    if curl -s "$url/api/tags" | grep -q "\"name\":\"$model\""; then
        print_success "Model '$model' is already available"
    else
        print_warning "Model '$model' not found. Pulling model..."
        curl -X POST "$url/api/pull" \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"$model\"}" || {
            print_error "Failed to pull model '$model'"
            return 1
        }
        print_success "Model '$model' pulled successfully"
    fi
}

# Main script
echo -e "${BLUE}"
echo "🚀 Ollama Translation API Startup"
echo "================================="
echo -e "${NC}"

# Check command line arguments
case "${1:-local}" in
    "local")
        print_info "Starting in LOCAL TESTING mode"
        
        # Copy local environment
        cp .env.local .env
        print_success "Using local environment configuration"
        
        # Check if Ollama is running locally
        if ! check_ollama "http://localhost:11434"; then
            print_warning "Ollama is not running locally"
            print_info "Starting Ollama..."
            
            # Try to start Ollama
            if command -v ollama > /dev/null; then
                ollama serve &
                OLLAMA_PID=$!
                print_info "Ollama started with PID: $OLLAMA_PID"
                
                # Wait for Ollama to be ready
                if ! wait_for_ollama "http://localhost:11434"; then
                    kill $OLLAMA_PID 2>/dev/null || true
                    exit 1
                fi
            else
                print_error "Ollama is not installed. Please install with: brew install ollama"
                exit 1
            fi
        else
            print_success "Ollama is already running locally"
        fi
        
        # Ensure model is available
        ensure_model "http://localhost:11434" "llama3.2"
        
        # Start FastAPI in local mode
        print_info "Starting FastAPI server in local mode..."
        exec ./venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
        ;;
        
    "docker")
        print_info "Starting in DOCKER CONTAINER mode"
        
        # Copy docker environment
        cp .env.docker .env
        print_success "Using Docker environment configuration"
        
        # Start Docker containers
        print_info "Starting Docker containers..."
        docker-compose up -d
        
        # Wait for Ollama container to be ready
        if ! wait_for_ollama "http://localhost:11434"; then
            print_error "Ollama container failed to start"
            docker-compose logs ollama
            exit 1
        fi
        
        # Ensure model is available in container
        ensure_model "http://localhost:11434" "llama3.2"
        
        print_success "All containers are running!"
        print_info "API available at: https://localhost:443"
        print_info "Health check: https://localhost:443/health"
        
        # Show container status
        docker-compose ps
        ;;
        
    "stop")
        print_info "Stopping all services..."
        
        # Stop Docker containers
        docker-compose down
        
        # Kill local Ollama if running
        pkill -f "ollama serve" 2>/dev/null || true
        
        print_success "All services stopped"
        ;;
        
    "status")
        print_info "Checking service status..."
        
        # Check local Ollama
        if check_ollama "http://localhost:11434"; then
            print_success "Local Ollama: Running"
        else
            print_warning "Local Ollama: Not running"
        fi
        
        # Check Docker containers
        if docker-compose ps | grep -q "Up"; then
            print_success "Docker containers: Running"
            docker-compose ps
        else
            print_warning "Docker containers: Not running"
        fi
        ;;
        
    "test")
        print_info "Running API tests..."
        
        # Generate test tokens
        ./venv/bin/python generate_test_tokens.py
        
        # Test health endpoint
        print_info "Testing health endpoint..."
        if curl -s http://localhost:8000/health | grep -q "healthy"; then
            print_success "Health check passed"
        else
            print_error "Health check failed"
        fi
        ;;
        
    *)
        echo "Usage: $0 {local|docker|stop|status|test}"
        echo ""
        echo "Commands:"
        echo "  local   - Start in local testing mode with fake Google tokens"
        echo "  docker  - Start in Docker container mode with real Google tokens"
        echo "  stop    - Stop all services"
        echo "  status  - Check status of all services"
        echo "  test    - Run API tests and generate tokens"
        exit 1
        ;;
esac
