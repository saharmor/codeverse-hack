# CodeVerse - Smart Code Planning with Claude Code

## Architecture Overview

CodeVerse is a full-stack macOS application that enables intelligent code planning through iterative collaboration with Claude Code. The system facilitates feature planning, code analysis, and implementation guidance through a conversational interface.

### Core Components

1. **Frontend (macOS Native App)**
   - Tauri-based interface for user interaction
   - Real-time chat interface for clarifying questions
   - Interactive plan artifact viewer with versioning
   - WebSocket client for streaming responses

2. **Backend (FastAPI + WebSockets)**
   - RESTful API for data management
   - WebSocket server for real-time communication
   - Claude Code integration for plan generation
   - Database management for repos and plans

3. **Database (PostgreSQL/SQLite)**
   - Repository metadata storage
   - Plan versioning and history
   - User session management

## Database Schema

See [schema.md](schema.md) for detailed database schema definitions.

## Backend Architecture (FastAPI)

### Core Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py              # Configuration settings
│   ├── database.py            # Database connection and models
│   ├── models/                # Pydantic models
│   │   ├── __init__.py
│   │   ├── repository.py
│   │   ├── plan.py
│   │   └── chat.py
│   ├── api/                   # REST API routes
│   │   ├── __init__.py
│   │   ├── repositories.py
│   │   ├── plans.py
│   │   └── chat.py
│   ├── websocket/             # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── manager.py         # WebSocket connection manager
│   │   └── handlers.py        # WebSocket event handlers
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── claude_integration.py
│   │   ├── plan_generator.py
│   │   └── repository_service.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── requirements.txt
└── docker-compose.yml
```

### Key Components

#### WebSocket Manager
- Manages client connections
- Handles real-time message broadcasting
- Supports room-based messaging (per plan/session)

#### Plan Generation Service
- Integrates with Claude Code CLI
- Processes user input and existing plans
- Generates specialized prompts for different planning phases
- Streams responses back to frontend

#### Repository Service
- Manages git repository metadata
- Handles repository discovery and validation
- Provides branch and commit information

## API Endpoints

### REST API

#### Repositories
- `GET /api/repositories` - List all repositories
- `POST /api/repositories` - Add new repository
- `GET /api/    /{repo_id}` - Get repository details
- `PUT /api/repositories/{repo_id}` - Update repository
- `DELETE /api/repositories/{repo_id}` - Remove repository

#### Plans
- `GET /api/repositories/{repo_id}/plans` - List plans for repository
- `POST /api/repositories/{repo_id}/plans` - Create new plan
- `GET /api/plans/{plan_id}` - Get plan details
- `PUT /api/plans/{plan_id}` - Update plan
- `DELETE /api/plans/{plan_id}` - Delete plan
- `GET /api/plans/{plan_id}/versions` - Get plan version history
- `POST /api/plans/{plan_id}/generate` - Trigger plan generation

#### Chat
- `GET /api/plans/{plan_id}/chat` - Get chat history
- `POST /api/plans/{plan_id}/chat/message` - Send chat message

### WebSocket Events

#### Client to Server
- `join_plan` - Join a plan's chat room
- `send_message` - Send chat message
- `generate_plan` - Request plan generation
- `update_artifact` - Update plan artifact

#### Server to Client
- `message_received` - New chat message
- `plan_generation_started` - Plan generation initiated
- `plan_generation_progress` - Streaming plan generation updates
- `plan_generation_completed` - Plan generation finished
- `artifact_updated` - Plan artifact updated
- `error` - Error occurred

## Frontend Architecture (macOS SwiftUI)

### Core Views

#### Main Window
- Repository selector
- Plan list with version history
- New plan creation

#### Plan Editor
- Split view: Chat interface + Plan artifact viewer
- Real-time updates via WebSocket
- Version comparison tools

#### Repository Manager
- Add/remove repositories
- Repository health status
- Branch selection

### Data Flow

1. **Initial Load**
   - Fetch repositories from backend
   - Display available plans per repository

2. **Plan Creation**
   - User selects repository and branch
   - Creates initial plan with description
   - Backend creates plan record and chat session

3. **Planning Iteration**
   - User sends message/question via chat
   - Frontend sends WebSocket message to backend
   - Backend calls `generate_plan()` with context
   - Claude Code generates response (streamed back)
   - Plan artifact updated in real-time
   - Chat history maintained

4. **Plan Versioning**
   - Each significant iteration creates new version
   - Users can compare versions
   - Rollback to previous versions possible

## Core Business Logic

### `generate_plan()` Function

```python
async def generate_plan(
    user_input: str,
    repository: Repository,
    existing_plan: Optional[Plan] = None,
    chat_history: List[ChatMessage] = [],
    branch: str = "main"
) -> AsyncIterator[str]:
    """
    Core function that orchestrates plan generation with Claude Code.

    Args:
        user_input: Latest user message/request
        repository: Target repository information
        existing_plan: Current plan (if iterating)
        chat_history: Previous conversation context
        branch: Target branch for implementation

    Yields:
        Streaming response from Claude Code
    """
```

## Claude CLI Configuration

### Setup Requirements

The backend requires Claude Code CLI to be installed and accessible. The system automatically detects Claude CLI from these locations (in order):

1. **~/.claude/local** - Official Claude CLI installation directory
2. **/usr/local/bin** - System-wide installation location
3. **~/node_modules/.bin** - npm local installation

### Custom Claude CLI Path

If your Claude CLI is installed in a different location, set the environment variable:

```bash
export CLAUDE_CLI_PATH=/path/to/your/claude/cli/directory
```

### Installation Methods

#### Official Claude CLI (Recommended)
Follow official installation instructions from Anthropic

#### npm Installation
```bash
npm install -g @anthropic-ai/claude-code
```

The system will automatically find and use the appropriate Claude CLI installation.
