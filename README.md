# Tauri + Next.js + FastAPI Boilerplate

A modern desktop application boilerplate that combines:

- **Tauri** - For native desktop functionality
- **Next.js** - For the frontend UI
- **FastAPI** - For the Python backend API

## 🚀 Features

- **Desktop App**: Native desktop application with Tauri
- **Modern UI**: Beautiful interface built with Next.js and Tailwind CSS
- **Python Backend**: Powerful API with FastAPI
- **Type Safety**: Full TypeScript support
- **Hot Reload**: Development with hot reload for both frontend and backend
- **Cross-platform**: Works on Windows, macOS, and Linux

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18 or later)
- **Python** (v3.8 or later)
- **Rust** (latest stable version)
- **Cargo** (comes with Rust)

### Installing Prerequisites

#### 1. Install Node.js

```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
nvm use node

# Or download from https://nodejs.org/
```

#### 2. Install Python

```bash
# macOS
brew install python

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Windows
# Download from https://python.org/
```

#### 3. Install Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

## 🛠️ Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Install frontend dependencies
npm install

# Install Tauri CLI globally
npm install -g @tauri-apps/cli

# Create Python virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 2. Start the Backend

```bash
# Start FastAPI backend
cd backend
python run.py
# Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 3. Start the Frontend

```bash
# In a new terminal, start Next.js frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. Run the Desktop App

```bash
# In a new terminal, run Tauri development
npm run tauri:dev
```

This will build and launch the desktop application.

## 📁 Project Structure

```
├── src/                    # Next.js frontend source
│   ├── app/               # Next.js app directory
│   │   ├── globals.css    # Global styles
│   │   ├── layout.tsx     # Root layout
│   │   └── page.tsx       # Main page
│   └── components/        # React components
├── src-tauri/             # Tauri backend (Rust)
│   ├── src/               # Rust source code
│   ├── Cargo.toml         # Rust dependencies
│   ├── build.rs           # Build configuration
│   └── tauri.conf.json    # Tauri configuration
├── backend/                # Python FastAPI backend
│   ├── main.py            # FastAPI application
│   ├── run.py             # Run script
│   └── requirements.txt   # Python dependencies
├── package.json            # Node.js dependencies
├── next.config.js          # Next.js configuration
├── tailwind.config.js      # Tailwind CSS configuration
└── README.md               # This file
```

## 🔧 Development

### Frontend Development

- **Next.js**: Modern React framework with app router
- **TypeScript**: Full type safety
- **Tailwind CSS**: Utility-first CSS framework
- **Tauri API**: Native desktop integration

### Backend Development

- **FastAPI**: Modern Python web framework
- **Pydantic**: Data validation
- **CORS**: Cross-origin resource sharing enabled
- **Hot Reload**: Automatic server restart on code changes

### Desktop Integration

- **Tauri Commands**: Custom Rust functions callable from frontend
- **Shell Integration**: Open external URLs and files
- **Window Management**: Configurable window properties

## 🚀 Available Scripts

```bash
# Frontend
npm run dev          # Start Next.js development server
npm run build        # Build Next.js for production
npm run start        # Start Next.js production server

# Tauri
npm run tauri:dev    # Start Tauri development
npm run tauri:build  # Build Tauri for production

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py        # Start FastAPI server
```

## 🌐 API Endpoints

The FastAPI backend provides these endpoints:

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `GET /api/users` - List all users
- `POST /api/users` - Create a new user
- `GET /api/users/{id}` - Get user by ID
- `GET /api/messages` - List all messages
- `POST /api/messages` - Create a new message
- `GET /api/stats` - Get application statistics

## 🔒 Security Features

- CORS configuration for frontend-backend communication
- Input validation with Pydantic models
- Error handling with proper HTTP status codes

## 📦 Building for Production

### Build the Frontend

```bash
npm run build
```

### Build the Desktop App

```bash
npm run tauri:build
```

The built application will be available in `src-tauri/target/release/`.

## 🐛 Troubleshooting

### Common Issues

1. **Tauri build fails**

   - Ensure Rust is properly installed: `rustc --version`
   - Check Cargo installation: `cargo --version`

2. **Python backend won't start**

   - Verify Python version: `python --version`
   - Check virtual environment activation
   - Install dependencies: `pip install -r requirements.txt`

3. **Frontend build issues**

   - Clear Next.js cache: `rm -rf .next`
   - Reinstall dependencies: `rm -rf node_modules && npm install`

4. **CORS errors**
   - Ensure backend is running on port 8000
   - Check CORS configuration in `backend/main.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [Tauri](https://tauri.app/) - For the desktop framework
- [Next.js](https://nextjs.org/) - For the React framework
- [FastAPI](https://fastapi.tiangolo.com/) - For the Python backend
- [Tailwind CSS](https://tailwindcss.com/) - For the styling framework

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Search existing issues
3. Create a new issue with detailed information

---

Happy coding! 🎉
