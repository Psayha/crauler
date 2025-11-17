#!/bin/bash
set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_message "$BLUE" "═══════════════════════════════════════════════════════════════"
    print_message "$GREEN" "  $1"
    print_message "$BLUE" "═══════════════════════════════════════════════════════════════"
    echo ""
}

print_step() {
    print_message "$BLUE" "➜ $1"
}

print_success() {
    print_message "$GREEN" "✅ $1"
}

print_warning() {
    print_message "$YELLOW" "⚠️  $1"
}

print_error() {
    print_message "$RED" "❌ $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup function
main() {
    print_header "AI Agency - Automated Setup Script"

    # Step 1: Check prerequisites
    print_step "Checking prerequisites..."

    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed"

    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed"

    if ! command_exists make; then
        print_warning "Make is not installed. You can still use docker-compose commands directly."
    else
        print_success "Make is installed"
    fi

    echo ""

    # Step 2: Create .env file if it doesn't exist
    print_step "Setting up environment variables..."

    if [ ! -f .env ]; then
        print_message "$YELLOW" "Creating .env file from .env.example..."
        cp .env.example .env
        print_success ".env file created"
        echo ""
        print_warning "IMPORTANT: You need to configure your .env file!"
        echo ""
        echo "Required variables to set:"
        echo "  1. CLAUDE_API_KEY - Get from https://console.anthropic.com/"
        echo "  2. TELEGRAM_BOT_TOKEN - Get from @BotFather on Telegram"
        echo "  3. JWT_SECRET_KEY - Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        echo ""
        read -p "Press Enter to open .env file in editor..."

        # Try to open editor
        if command_exists nano; then
            nano .env
        elif command_exists vi; then
            vi .env
        elif command_exists vim; then
            vim .env
        else
            print_warning "No editor found. Please manually edit .env file"
        fi
    else
        print_success ".env file already exists"
    fi

    echo ""

    # Step 3: Verify Claude API key
    print_step "Verifying configuration..."

    if grep -q "your-claude-api-key-here" .env; then
        print_error "CLAUDE_API_KEY is not set in .env file"
        echo "Please set your Claude API key and run this script again"
        exit 1
    fi
    print_success "Configuration looks good"

    echo ""

    # Step 4: Check if Docker daemon is running
    print_step "Checking Docker daemon..."

    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker daemon is running"

    echo ""

    # Step 5: Stop any existing containers
    print_step "Cleaning up existing containers..."

    docker-compose down > /dev/null 2>&1 || true
    print_success "Cleanup complete"

    echo ""

    # Step 6: Build Docker images
    print_header "Building Docker Images"
    print_step "This may take several minutes on first run..."
    echo ""

    if docker-compose build --no-cache; then
        print_success "Docker images built successfully"
    else
        print_error "Failed to build Docker images"
        exit 1
    fi

    echo ""

    # Step 7: Start services
    print_header "Starting Services"
    print_step "Starting PostgreSQL, Redis, and Backend..."
    echo ""

    if docker-compose up -d; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi

    echo ""

    # Step 8: Wait for services to be healthy
    print_step "Waiting for services to be ready..."

    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker-compose exec -T postgres pg_isready -U aiagency > /dev/null 2>&1; then
            break
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        echo ""
        print_error "Services failed to become ready"
        echo ""
        echo "Check logs with: docker-compose logs"
        exit 1
    fi

    echo ""
    print_success "All services are ready"

    echo ""

    # Step 9: Display service information
    print_header "Setup Complete! 🎉"

    echo "Services are running:"
    echo ""
    print_message "$GREEN" "  Backend API:    http://localhost:8000"
    print_message "$GREEN" "  API Docs:       http://localhost:8000/docs"
    print_message "$GREEN" "  ReDoc:          http://localhost:8000/redoc"
    print_message "$GREEN" "  PostgreSQL:     localhost:5432"
    print_message "$GREEN" "  Redis:          localhost:6379"
    echo ""

    print_message "$BLUE" "Useful commands:"
    echo ""
    echo "  make help           - Show all available commands"
    echo "  make logs           - View all logs"
    echo "  make logs-backend   - View backend logs"
    echo "  make shell          - Open backend shell"
    echo "  make shell-db       - Open database shell"
    echo "  make down           - Stop all services"
    echo "  make restart        - Restart services"
    echo "  make health         - Check service health"
    echo ""

    print_message "$YELLOW" "Next steps:"
    echo ""
    echo "  1. Visit http://localhost:8000/docs to explore the API"
    echo "  2. Create your first project via API or Swagger UI"
    echo "  3. Setup Telegram Mini App (see README.md)"
    echo "  4. Install frontend dependencies: cd frontend && npm install"
    echo ""

    print_message "$GREEN" "Happy coding! 🚀"
    echo ""
}

# Run main function
main "$@"
