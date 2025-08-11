# CodeVerse

A desktop application that transforms how developers plan and execute code projects through intelligent AI assistance and natural voice interaction.

Video here https://drive.google.com/drive/folders/13URKjQBmcLB1vFVDTHrCpZPUVxgit66U?usp=sharing

## What is CodeVerse?

CodeVerse is an AI-powered development companion that helps you break down complex coding projects into actionable plans. Simply describe your project goals through text or voice, and CodeVerse generates comprehensive development plans while providing an interactive chat interface to refine your approach.

**Key Features:**
- AI-powered project planning with Claude integration
- Voice-to-text input for hands-free planning
- Interactive chat interface for plan refinement
- Repository and plan version management
- Clean, resizable three-panel desktop interface

## Prerequisites

- **Node.js** (v18 or later)
- **Python** (v3.8 or later) 
- **Rust** (latest stable version)
- **Claude CLI** - Install from [Claude AI](https://claude.ai/chat)

## Installation

### 1. Clone and Install Dependencies

```bash
# Install frontend dependencies
npm install

# Install Tauri CLI
npm install -g @tauri-apps/cli

# Set up Python backend
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 2. Configure Environment

Copy `env.example` to `.env` and configure your settings:

```bash
cp env.example .env
```

Add your API keys:
- OpenAI API key for transcription (optional)
- Claude API access via Claude CLI

### 3. Initialize Database

```bash
cd backend
source .venv/bin/activate
python setup_db.py
cd ..
```

## Running the Application

### Start All Services

```bash
# Terminal 1: Start the backend API
cd backend
source .venv/bin/activate
python run.py

# Terminal 2: Start the desktop application
npm run tauri:dev
```

The backend runs on `http://localhost:8000` and the desktop app will launch automatically.

## Usage

1. **Create a Repository**: Add your project directory to start planning
2. **Voice or Text Input**: Describe your coding goals using the microphone or text input
3. **Review AI Plans**: CodeVerse generates structured development plans
4. **Interactive Refinement**: Use the chat interface to ask questions and refine plans
5. **Track Progress**: Manage multiple plan versions as your project evolves

## Architecture

**Frontend**: Next.js with TypeScript and Tailwind CSS
**Backend**: FastAPI with SQLAlchemy
**Desktop**: Tauri for native desktop integration
**AI**: Claude Code SDK for intelligent planning
**Database**: SQLite for local data storage

## Development

### Build for Production

```bash
# Build the desktop application
npm run tauri:build
```

The built application will be in `src-tauri/target/release/`.

### Testing

```bash
# Run backend tests
cd backend
source .venv/bin/activate
python -m pytest tests/

# Run frontend tests
npm test
```

## Project Structure

```
├── src/                    # Next.js frontend
│   ├── app/               # App router pages
│   └── components/        # React components
├── backend/               # FastAPI backend
│   ├── models/           # Database models
│   ├── routers/          # API routes
│   └── services/         # Business logic
├── src-tauri/            # Tauri desktop app
└── scripts/              # Build and utility scripts
```

## License

MIT License - see LICENSE file for details.