# Migration Notes - November 2025 Update

This document outlines the major dependency updates and breaking changes in the November 2025 update.

## 📋 Overview

This update brings all dependencies to their latest stable versions as of November 2025, including major version upgrades for several key libraries.

## 🔄 Major Version Updates

### Backend

| Package | Old Version | New Version | Change |
|---------|-------------|-------------|--------|
| Python | 3.11 | 3.13 | **Major** |
| FastAPI | 0.104.1 | 0.121.2 | Minor |
| Anthropic SDK | 0.7.0 | 0.73.0 | **Critical - 66 versions!** |
| Pydantic | 2.5.0 | 2.12.3 | Minor |
| SQLAlchemy | 2.0.23 | 2.0.44 | Patch |
| Uvicorn | 0.24.0 | 0.38.0 | Minor |
| Celery | 5.3.4 | 5.5.3 | Minor |
| PostgreSQL | 15 | 17 | **Major** |
| Redis | 7 | 8 | **Major** |

### Frontend

| Package | Old Version | New Version | Change |
|---------|-------------|-------------|--------|
| Next.js | 14.2.0 | 15.5.1 | **Major** |
| React | 18.2.0 | 19.2.0 | **Major** |
| React DOM | 18.2.0 | 19.2.0 | **Major** |
| TanStack Query | 5.28.0 | 5.90.10 | Minor |
| Telegram SDK | 1.1.0 | 2.10.0 | **Major** |
| TypeScript | 5.4.2 | 5.7.2 | Minor |

## ⚠️ Breaking Changes

### Python 3.13

**What's New:**
- Free-threading support (experimental GIL removal)
- JIT compiler improvements
- Better error messages

**Breaking Changes:**
- Some deprecated APIs removed
- Changed behavior in `typing` module
- Updated C API

**Migration Steps:**
1. Update Docker base image: `FROM python:3.13-slim`
2. Test all imports and type hints
3. Review deprecation warnings in logs

### React 19

**What's New:**
- React Server Components improvements
- Actions and useFormState
- New `use()` hook for promises
- Improved error handling

**Breaking Changes:**
- `defaultProps` removed for function components (use ES6 default parameters)
- Some legacy Context API changes
- Ref handling updated

**Migration Steps:**
1. Replace `defaultProps` with default parameters:
```typescript
// Old
function Component(props) { ... }
Component.defaultProps = { name: 'Guest' }

// New
function Component({ name = 'Guest' }) { ... }
```

2. Update ref forwarding if needed
3. Test all component renders

### Next.js 15

**What's New:**
- Turbopack stable for dev (added `--turbopack` flag)
- Partial Prerendering
- Enhanced caching strategies
- Better TypeScript support

**Breaking Changes:**
- Some middleware API changes
- Updated image optimization defaults
- Changed behavior in `next/link`

**Migration Steps:**
1. Update `next.config.js` if you have custom webpack config
2. Test all routes and navigation
3. Review image optimization settings
4. Use Turbopack for faster dev: `next dev --turbopack`

### FastAPI 0.121.2

**What's New:**
- Better Pydantic v2 integration
- Performance improvements
- Enhanced WebSocket support

**Breaking Changes:**
- Minor API refinements
- Updated dependency resolution

**Migration Steps:**
1. Update command to use new `fastapi` CLI:
```bash
# Old
uvicorn app.main:app --reload

# New
fastapi dev app/main.py
```

2. Review any custom middleware
3. Test all API endpoints

### Anthropic SDK 0.73.0

**What's New:**
- Latest Claude models support
- Streaming improvements
- Better error handling
- New rate limit handling

**Critical Update:**
This was **66 versions behind** - critical security and feature updates!

**Migration Steps:**
1. Review API client instantiation
2. Update error handling for new exception types
3. Test all Claude API calls
4. Review streaming implementations

### PostgreSQL 17

**What's New:**
- Performance improvements
- Better JSON support
- Enhanced partitioning

**Breaking Changes:**
- Some SQL syntax changes
- Updated replication features

**Migration Steps:**
1. Backup your database before upgrading
2. Test all queries
3. Review any custom SQL functions
4. Check index performance

### Redis 8

**What's New:**
- Performance improvements
- New data structures
- Enhanced clustering

**Breaking Changes:**
- Some command deprecations
- Updated configuration options

**Migration Steps:**
1. Review Redis commands usage
2. Test cache operations
3. Check Celery integration

## 🔧 Docker Configuration Changes

### Dockerfile Updates

**Backend (`docker/Dockerfile.backend`):**
```dockerfile
# Old
FROM python:3.11-slim

# New
FROM python:3.13-slim

# Added healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Updated CMD to use fastapi CLI
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Updates

**docker-compose.yml:**
```yaml
# PostgreSQL
postgres:
  image: postgres:17-alpine  # Was: postgres:15-alpine
  restart: unless-stopped    # Added

# Redis
redis:
  image: redis:8-alpine      # Was: redis:7-alpine
  restart: unless-stopped    # Added

# Backend
backend:
  command: fastapi dev app/main.py --host 0.0.0.0 --port 8000
  restart: unless-stopped    # Added
  environment:
    JWT_SECRET_KEY: ${JWT_SECRET_KEY:-change-this-in-production}
    TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:-}
```

## 📦 New Dependencies

### Backend
- `langchain-community==0.3.17` - Community integrations
- `langchain-openai==0.3.1` - OpenAI integrations (optional)

### Frontend
- All dependencies updated to latest compatible versions
- No new dependencies added

## 🚀 Migration Steps

### Full Migration (Recommended)

1. **Backup everything:**
```bash
# Backup database
docker-compose exec postgres pg_dump -U aiagency ai_agency > backup.sql

# Backup .env file
cp .env .env.backup
```

2. **Pull latest code:**
```bash
git pull origin main
```

3. **Rebuild containers:**
```bash
docker-compose down -v  # WARNING: This removes volumes
docker-compose build --no-cache
docker-compose up -d
```

4. **Restore data if needed:**
```bash
cat backup.sql | docker-compose exec -T postgres psql -U aiagency ai_agency
```

5. **Test all functionality:**
- Create test project via API
- Execute project
- Check WebSocket connections
- Test Telegram authentication

### Incremental Migration (If you have production data)

1. **Test in development first:**
```bash
# Create separate docker-compose.dev.yml
# Test all changes there
```

2. **Update backend only:**
```bash
docker-compose build backend
docker-compose up -d backend
```

3. **Update database (with backup):**
```bash
# Stop backend first
docker-compose stop backend

# Upgrade PostgreSQL
docker-compose up -d postgres

# Restart backend
docker-compose up -d backend
```

4. **Monitor logs:**
```bash
docker-compose logs -f backend
```

### Frontend Migration

1. **Update dependencies:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

2. **Test locally:**
```bash
npm run dev
```

3. **Check for React 19 issues:**
- Look for `defaultProps` usage
- Test all forms and interactions
- Verify Telegram SDK integration

4. **Build and deploy:**
```bash
npm run build
```

## 🧪 Testing Checklist

After migration, test:

- [ ] Backend starts without errors
- [ ] Database connections work
- [ ] Redis connections work
- [ ] All API endpoints respond
- [ ] Claude API integration works
- [ ] WebSocket connections establish
- [ ] Telegram authentication works
- [ ] Frontend loads in Telegram Mini App
- [ ] Real-time updates work
- [ ] Project creation and execution
- [ ] All 10 agents execute properly

## 📚 Additional Resources

### Documentation Links

- [Python 3.13 What's New](https://docs.python.org/3.13/whatsnew/3.13.html)
- [React 19 Upgrade Guide](https://react.dev/blog/2024/12/05/react-19)
- [Next.js 15 Upgrade Guide](https://nextjs.org/docs/app/building-your-application/upgrading/version-15)
- [FastAPI Latest Docs](https://fastapi.tiangolo.com/)
- [Anthropic SDK Docs](https://docs.anthropic.com/)
- [PostgreSQL 17 Release Notes](https://www.postgresql.org/docs/17/release-17.html)
- [Redis 8 Release Notes](https://redis.io/docs/latest/operate/oss_and_stack/install/upgrade/)

## 🐛 Known Issues

### None currently identified

If you encounter issues after migration, please:
1. Check logs: `docker-compose logs -f`
2. Verify environment variables in `.env`
3. Ensure Claude API key is valid
4. Check Docker has enough resources

## 💡 Performance Improvements

After this update, you should see:

- **Faster dev builds** with Turbopack (Next.js 15)
- **Better API performance** with FastAPI 0.121.2
- **Improved database queries** with PostgreSQL 17
- **Lower memory usage** with Python 3.13 optimizations
- **Better Claude API reliability** with SDK 0.73.0

## ⏭️ Future Updates

To stay up-to-date:

1. Check [context7.com](https://context7.com/) for latest package versions
2. Monitor Anthropic SDK releases (critical for AI features)
3. Subscribe to Next.js and React release notes
4. Review PostgreSQL and Redis changelogs

## 🆘 Rollback Instructions

If something goes wrong:

```bash
# Stop all containers
docker-compose down

# Restore .env backup
cp .env.backup .env

# Checkout previous version
git checkout <previous-commit-hash>

# Rebuild
docker-compose build --no-cache
docker-compose up -d

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U aiagency ai_agency
```

---

**Last Updated:** November 17, 2025
**Prepared by:** AI Agency Development Team
