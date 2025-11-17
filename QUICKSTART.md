# 🚀 Quick Start Guide

Get AI Agency up and running in **5 minutes**!

## Prerequisites

- ✅ Docker & Docker Compose installed
- ✅ Claude API key ([Get here](https://console.anthropic.com/))
- ✅ (Optional) Telegram Bot Token ([Create via @BotFather](https://t.me/BotFather))

## One-Command Setup

```bash
./setup.sh
```

That's it! The script will:
1. ✅ Check prerequisites
2. ✅ Create .env configuration
3. ✅ Build Docker images
4. ✅ Start all services
5. ✅ Run database migrations
6. ✅ Verify everything works

## Manual Setup (Alternative)

If you prefer manual control:

### 1. Clone & Configure

```bash
git clone <repository-url>
cd crauler

# Create environment file
cp .env.example .env

# Edit .env and add your Claude API key
nano .env  # or use your preferred editor
```

### 2. Deploy

```bash
# Using Make (recommended)
make deploy

# Or using Docker Compose directly
docker-compose build --no-cache
docker-compose up -d
```

### 3. Verify

```bash
# Check service health
make health

# Or manually
curl http://localhost:8000/health
```

## Access Your Services

| Service | URL | Description |
|---------|-----|-------------|
| **Backend API** | http://localhost:8000 | FastAPI backend |
| **API Docs (Swagger)** | http://localhost:8000/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8000/redoc | Alternative API docs |
| **PostgreSQL** | localhost:5432 | Database (user: aiagency) |
| **Redis** | localhost:6379 | Cache & message broker |

## Quick Test

Create your first project:

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a landing page for AI consulting company",
    "organization_id": "test-org"
  }'
```

Or use the interactive Swagger UI at http://localhost:8000/docs

## Frontend Setup (Telegram Mini App)

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:3000

See [frontend/README.md](frontend/README.md) for full setup including Telegram integration.

## Useful Commands

```bash
make help           # Show all available commands
make logs           # View logs from all services
make logs-backend   # View only backend logs
make shell          # Open backend container shell
make shell-db       # Open PostgreSQL shell
make down           # Stop all services
make restart        # Restart all services
make clean          # Stop and remove everything
```

## Troubleshooting

### Services won't start?

```bash
# Check Docker is running
docker info

# View detailed logs
make logs

# Restart everything
make down && make up
```

### Database connection errors?

```bash
# Reset database (⚠️ destroys all data)
make db-reset
```

### Port already in use?

Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001 or another port
```

## What's Next?

1. 📖 Read the [full README](README.md) for detailed documentation
2. 🔄 Check [MIGRATION_NOTES.md](MIGRATION_NOTES.md) if updating from older version
3. 🎨 Customize agents in `backend/app/agents/`
4. 📱 Setup Telegram Mini App (see [Telegram Setup](#telegram-setup))
5. 🚀 Deploy to production (see [Deployment Guide](#production-deployment))

## Telegram Setup

### 1. Create Bot

1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the bot token

### 2. Configure

Add token to `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. Create Mini App

1. Send `/newapp` to @BotFather
2. Select your bot
3. Provide app details:
   - Name: AI Agency
   - URL: https://your-vercel-app.vercel.app
   - Upload icon (640x360px)

### 4. Deploy Frontend

```bash
cd frontend

# Deploy to Vercel
vercel --prod

# Or use your preferred hosting
npm run build
```

Update `.env` with production URL:
```env
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
```

## Production Deployment

### Quick Production Setup

```bash
# 1. Update .env for production
sed -i 's/DEBUG=true/DEBUG=false/g' .env
sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/g' .env

# 2. Generate secure secrets
python -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_urlsafe(32)}')"

# 3. Deploy
make deploy
```

### Production Checklist

- [ ] Set `DEBUG=false` in `.env`
- [ ] Use strong `DATABASE_URL` password
- [ ] Generate secure `JWT_SECRET_KEY`
- [ ] Enable HTTPS for all URLs
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Setup SSL certificates
- [ ] Enable monitoring (Sentry, etc.)
- [ ] Setup database backups
- [ ] Configure rate limiting
- [ ] Setup log aggregation

## Architecture Overview

```
┌─────────────────────────────────────┐
│   Telegram Mini App (Next.js 15)   │
│   React 19 + TypeScript 5.7         │
└──────────────┬──────────────────────┘
               │ HTTPS/WSS
┌──────────────▼──────────────────────┐
│   Backend API (FastAPI 0.121.2)    │
│   Python 3.13                       │
│   ├─ 10 AI Agents (Claude)          │
│   ├─ REST API + WebSocket           │
│   └─ Orchestrator Engine            │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   PostgreSQL 17 + Redis 8           │
└─────────────────────────────────────┘
```

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | FastAPI | 0.121.2 |
| Language | Python | 3.13 |
| AI | Anthropic Claude | Latest |
| Database | PostgreSQL | 17 |
| Cache | Redis | 8 |
| Frontend | Next.js | 15.5.1 |
| UI Library | React | 19.2.0 |
| ORM | SQLAlchemy | 2.0.44 |
| Migrations | Alembic | 1.14.2 |

## Support

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/your-repo/issues)
- 💬 [Discussions](https://github.com/your-repo/discussions)
- 📧 Email: support@your-domain.com

## License

MIT License - See [LICENSE](LICENSE) file for details

---

**Ready to build amazing projects with AI?** 🚀

Start by visiting http://localhost:8000/docs and create your first project!
