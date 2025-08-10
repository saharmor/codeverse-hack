# Database Schema

## Tables

### `repositories`
```sql
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    git_url TEXT,
    default_branch VARCHAR(100) DEFAULT 'main',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(path)
);
```

### `plans`
```sql
CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_branch VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    status ENUM('draft', 'active', 'completed', 'archived') DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, name, version)
);
```

### `plan_artifacts`
```sql
CREATE TABLE plan_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    content JSONB NOT NULL,
    artifact_type ENUM('feature_plan', 'implementation_steps', 'code_changes') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `chat_sessions`
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    messages JSONB NOT NULL DEFAULT '[]',
    status ENUM('active', 'completed') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Database Design Rationale

### Repositories Table
- Stores metadata about git repositories being managed
- `path` is unique to prevent duplicate repository entries
- `git_url` allows for remote repository tracking
- `default_branch` enables flexible branch management

### Plans Table
- Linked to repositories via foreign key relationship
- Version-controlled with integer versioning
- Status tracking for plan lifecycle management
- Unique constraint on (repository_id, name, version) prevents conflicts

### Plan Artifacts Table
- JSONB content allows flexible artifact storage
- Different artifact types support various planning phases
- One-to-many relationship with plans for artifact history

### Chat Sessions Table
- JSONB messages array for flexible message storage
- Status tracking for active vs completed conversations
- Linked to plans for context preservation

## Migration Strategy

### Development
- Use SQLite for local development
- Alembic migrations for schema evolution

### Production
- PostgreSQL for production deployment
- Full ACID compliance and concurrent access support
- JSONB indexing for efficient artifact queries

## Indexing Strategy

```sql
-- Performance indexes
CREATE INDEX idx_repositories_path ON repositories(path);
CREATE INDEX idx_plans_repository_status ON plans(repository_id, status);
CREATE INDEX idx_plans_version ON plans(repository_id, name, version);
CREATE INDEX idx_plan_artifacts_plan_type ON plan_artifacts(plan_id, artifact_type);
CREATE INDEX idx_chat_sessions_plan_status ON chat_sessions(plan_id, status);

-- JSONB indexes for artifact content
CREATE INDEX idx_plan_artifacts_content_gin ON plan_artifacts USING gin(content);
CREATE INDEX idx_chat_messages_gin ON chat_sessions USING gin(messages);
```
