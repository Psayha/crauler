# AI Agency API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
Все endpoints (кроме `/`, `/health`, `/api/auth/telegram`) требуют JWT токен:
```
Authorization: Bearer {token}
```

## Endpoints

### Authentication
```
POST   /api/auth/telegram      - Telegram Auth (получить JWT)
GET    /api/auth/me            - Current User
POST   /api/auth/logout        - Logout
```

### Projects
```
GET    /api/projects           - List all projects
POST   /api/projects           - Create project (auto-decomposition)
GET    /api/projects/{id}      - Project details + tasks
GET    /api/projects/{id}/status - Project status
GET    /api/projects/{id}/progress - Execution progress
POST   /api/projects/{id}/execute - Start execution
```

### Tasks
```
GET    /api/tasks/{id}                - Task details
GET    /api/tasks/project/{project_id} - Project tasks
POST   /api/tasks/{id}/execute         - Execute task
POST   /api/tasks/{id}/retry           - Retry failed task
```

### Agents
```
GET    /api/agents             - List all agents (11)
GET    /api/agents/{type}      - Agent info
```

### HR Agent
```
GET    /api/hr/agents/performance               - All agents metrics
GET    /api/hr/agents/{type}/performance        - Agent metrics
POST   /api/hr/agents/{type}/analyze            - Analyze agent
POST   /api/hr/agents/{type}/suggest-improvements - Suggest improvements
GET    /api/hr/improvements                     - Improvements history
POST   /api/hr/analyze-skill-gaps               - Analyze skill gaps
POST   /api/hr/recruit-agent                    - Create new agent
GET    /api/hr/dynamic-agents                   - Dynamic agents list
DELETE /api/hr/dynamic-agents/{id}              - Delete dynamic agent
```

### Knowledge Base
```
POST   /api/knowledge/search           - Semantic search
POST   /api/knowledge/store            - Store knowledge
GET    /api/knowledge/similar/{id}     - Similar entries
POST   /api/knowledge/context          - Agent context
POST   /api/knowledge/suggest-projects - Project suggestions
GET    /api/knowledge/stats            - Knowledge stats
```

### Notifications
```
GET    /api/notifications               - Activity feed (filter: project/task/agent/system)
GET    /api/notifications/unread-count  - Unread count
```

### WebSocket
```
WS     /ws?token={jwt}          - Real-time updates
```

### Health
```
GET    /                        - Service info
GET    /health                  - Health check
```

## Request Examples

### Create Project
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"description": "Create a landing page with contact form"}'
```

### Execute Project
```bash
curl -X POST http://localhost:8000/api/projects/{id}/execute \
  -H "Authorization: Bearer {token}"
```

### Search Knowledge
```bash
curl -X POST http://localhost:8000/api/knowledge/search \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"query": "React hooks", "top_k": 5}'
```

## Interactive Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
