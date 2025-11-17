#!/bin/bash
set -e

echo "🚀 Starting AI Agency Backend..."

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo "⏳ Waiting for PostgreSQL to be ready..."

    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if pg_isready -h postgres -U aiagency > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready!"
            return 0
        fi

        attempt=$((attempt + 1))
        echo "   Attempt $attempt/$max_attempts - PostgreSQL not ready yet, waiting..."
        sleep 2
    done

    echo "❌ PostgreSQL failed to become ready in time"
    exit 1
}

# Function to wait for Redis
wait_for_redis() {
    echo "⏳ Waiting for Redis to be ready..."

    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if redis-cli -h redis ping > /dev/null 2>&1; then
            echo "✅ Redis is ready!"
            return 0
        fi

        attempt=$((attempt + 1))
        echo "   Attempt $attempt/$max_attempts - Redis not ready yet, waiting..."
        sleep 2
    done

    echo "❌ Redis failed to become ready in time"
    exit 1
}

# Function to run database migrations
run_migrations() {
    echo "🔄 Running database migrations..."

    cd /app

    # Check if alembic is configured
    if [ ! -f "alembic.ini" ]; then
        echo "❌ alembic.ini not found!"
        exit 1
    fi

    # Run migrations
    if alembic upgrade head; then
        echo "✅ Database migrations completed successfully!"
    else
        echo "❌ Database migrations failed!"
        exit 1
    fi
}

# Function to check environment variables
check_env_vars() {
    echo "🔍 Checking required environment variables..."

    required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "CLAUDE_API_KEY"
    )

    missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo "❌ Missing required environment variables:"
        printf '   - %s\n' "${missing_vars[@]}"
        echo ""
        echo "Please set these variables in your .env file or docker-compose.yml"
        exit 1
    fi

    echo "✅ All required environment variables are set!"
}

# Main execution flow
main() {
    echo ""
    echo "═══════════════════════════════════════"
    echo "    AI Agency Backend Initialization    "
    echo "═══════════════════════════════════════"
    echo ""

    # Step 1: Check environment variables
    check_env_vars
    echo ""

    # Step 2: Wait for PostgreSQL
    wait_for_postgres
    echo ""

    # Step 3: Wait for Redis
    wait_for_redis
    echo ""

    # Step 4: Run migrations
    run_migrations
    echo ""

    echo "═══════════════════════════════════════"
    echo "   🎉 Initialization Complete!          "
    echo "═══════════════════════════════════════"
    echo ""
    echo "🚀 Starting FastAPI server..."
    echo ""

    # Execute the command passed to the script (or default CMD from Dockerfile)
    exec "$@"
}

# Run main function with all arguments
main "$@"
