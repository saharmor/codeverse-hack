# Project Structure

This document provides a detailed overview of the Tauri + Next.js + FastAPI boilerplate project structure.

## 📁 Root Directory

```
codeverse-hack/
├── README.md                 # Main project documentation
├── PROJECT_STRUCTURE.md      # This file - detailed structure
├── package.json              # Node.js dependencies and scripts
├── next.config.js            # Next.js configuration
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.js        # Tailwind CSS configuration
├── postcss.config.js         # PostCSS configuration
├── .eslintrc.json            # ESLint configuration
├── .gitignore                # Git ignore patterns
├── env.example               # Environment variables template
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile.frontend       # Frontend Docker configuration
└── scripts/                  # Utility scripts
```

## 🎨 Frontend (Next.js)

### Source Directory: `src/`

```
src/
├── app/                      # Next.js 13+ app directory
│   ├── globals.css          # Global CSS with Tailwind
│   ├── layout.tsx           # Root layout component
│   └── page.tsx             # Main page component
├── components/               # Reusable React components
│   ├── Button.tsx           # Button component
│   └── StatusCard.tsx       # Status card component
└── lib/                     # Utility libraries
    └── api.ts               # API client utilities
```

### Key Frontend Files:

- **`src/app/page.tsx`**: Main application page with Tauri integration
- **`src/app/layout.tsx`**: Root layout with metadata and global styles
- **`src/app/globals.css`**: Global styles with Tailwind CSS imports
- **`src/components/`**: Reusable UI components
- **`src/lib/api.ts`**: API client for backend communication

## 🦀 Desktop (Tauri)

### Source Directory: `src-tauri/`

```
src-tauri/
├── src/
│   └── main.rs              # Main Rust application
├── Cargo.toml                # Rust dependencies and metadata
├── build.rs                  # Build configuration
└── tauri.conf.json          # Tauri application configuration
```

### Key Tauri Files:

- **`src-tauri/src/main.rs`**: Main Rust application with Tauri commands
- **`src-tauri/tauri.conf.json`**: Tauri app configuration (window, permissions, etc.)
- **`src-tauri/Cargo.toml`**: Rust dependencies and build settings

## 🐍 Backend (FastAPI)

### Source Directory: `backend/`

```
backend/
├── main.py                   # Main FastAPI application
├── run.py                    # Run script for development
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
└── Dockerfile                # Docker configuration
```

### Key Backend Files:

- **`backend/main.py`**: FastAPI application with API endpoints
- **`backend/config.py`**: Configuration management with environment variables
- **`backend/run.py`**: Development server runner
- **`backend/requirements.txt`**: Python package dependencies

## 🛠️ Scripts

### Scripts Directory: `scripts/`

```
scripts/
├── setup.sh                  # Initial project setup
├── dev.sh                    # Start development environment
└── build.sh                  # Build for production
```

### Script Functions:

- **`setup.sh`**: Checks prerequisites, installs dependencies, sets up Python environment
- **`dev.sh`**: Starts both backend and frontend development servers
- **`build.sh`**: Builds frontend and Tauri app for production

## 🐳 Docker Configuration

### Docker Files:

- **`docker-compose.yml`**: Orchestrates backend and frontend services
- **`backend/Dockerfile`**: Python FastAPI container
- **`Dockerfile.frontend`**: Next.js frontend container

### Docker Services:

- **Backend**: FastAPI server on port 8000
- **Frontend**: Next.js development server on port 3000

## 📱 Application Features

### Frontend Features:

- Modern React with Next.js 13+ app router
- TypeScript for type safety
- Tailwind CSS for styling
- Responsive design
- Tauri API integration
- Backend API communication

### Backend Features:

- FastAPI with automatic API documentation
- Pydantic models for data validation
- CORS configuration for frontend access
- Health check endpoints
- RESTful API design
- In-memory data storage (easily replaceable with database)

### Desktop Features:

- Native desktop application
- Custom Tauri commands
- Shell integration (open URLs)
- Configurable window properties
- Cross-platform compatibility

## 🔧 Configuration Files

### Next.js Configuration:

- **`next.config.js`**: Static export, image optimization, app directory
- **`tsconfig.json`**: TypeScript compiler options
- **`tailwind.config.js`**: Tailwind CSS customization
- **`postcss.config.js`**: PostCSS processing

### Tauri Configuration:

- **`tauri.conf.json`**: Window settings, permissions, build paths
- **`Cargo.toml`**: Rust dependencies and features

### Backend Configuration:

- **`config.py`**: Environment-based configuration
- **`requirements.txt`**: Python package versions

## 🚀 Development Workflow

### 1. Setup Phase:

```bash
# Run setup script
./scripts/setup.sh

# Or manual setup
npm install
cd backend && python -m venv .venv && pip install -r requirements.txt
```

### 2. Development Phase:

```bash
# Option 1: Use development script
./scripts/dev.sh

# Option 2: Manual start
# Terminal 1: Backend
cd backend && python run.py

# Terminal 2: Frontend
npm run dev

# Terminal 3: Desktop app
npm run tauri:dev
```

### 3. Build Phase:

```bash
# Build everything
./scripts/build.sh

# Or manual build
npm run build
npm run tauri:build
```

## 📊 API Endpoints

### Available Backend Endpoints:

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `GET /api/users/{id}` - Get user by ID
- `GET /api/messages` - List messages
- `POST /api/messages` - Create message
- `GET /api/stats` - Application statistics

## 🔒 Security & Permissions

### Tauri Permissions:

- Shell: `open` (for opening URLs)
- All other permissions disabled by default

### Backend Security:

- CORS configuration for frontend access
- Input validation with Pydantic
- Error handling with proper HTTP status codes

## 📦 Build Outputs

### Frontend Build:

- **Output Directory**: `./out/`
- **Format**: Static HTML/CSS/JS files
- **Optimization**: Tailwind CSS purged, images optimized

### Desktop Build:

- **Output Directory**: `./src-tauri/target/release/`
- **Formats**: Platform-specific executables
- **Platforms**: Windows (.exe), macOS (.app), Linux (binary)

## 🧪 Testing & Development

### Development Tools:

- **Hot Reload**: Both frontend and backend support hot reloading
- **Type Checking**: TypeScript compilation and checking
- **Linting**: ESLint for code quality
- **Formatting**: Prettier-ready configuration

### Debugging:

- **Frontend**: Browser DevTools, Next.js debugging
- **Backend**: FastAPI automatic documentation, logging
- **Desktop**: Tauri DevTools, Rust debugging

## 🔄 Deployment Options

### 1. Local Development:

- All services run locally
- Hot reload enabled
- Easy debugging

### 2. Docker Development:

- Containerized services
- Consistent environment
- Easy service orchestration

### 3. Production Build:

- Static frontend export
- Compiled desktop application
- Standalone backend server

## 📚 Additional Resources

### Documentation:

- **Tauri**: https://tauri.app/
- **Next.js**: https://nextjs.org/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Tailwind CSS**: https://tailwindcss.com/

### Community:

- **Tauri Discord**: https://discord.gg/tauri
- **Next.js GitHub**: https://github.com/vercel/next.js
- **FastAPI GitHub**: https://github.com/tiangolo/fastapi

---

This structure provides a solid foundation for building modern desktop applications with web technologies and Python backends. The modular design allows for easy customization and extension based on specific project requirements.
