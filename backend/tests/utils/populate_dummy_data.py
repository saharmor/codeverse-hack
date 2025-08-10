#!/usr/bin/env python3
"""
Dummy data population script for CodeVerse

This script creates dummy repositories and populates the database with sample data.
It supports both creation and cleanup functions.

Usage:
    python scripts/populate_dummy_data.py create    # Create dummy repos and populate DB
    python scripts/populate_dummy_data.py cleanup   # Clean up dummy repos and DB entries
    python scripts/populate_dummy_data.py reset     # Cleanup then create (full reset)
"""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

# Add the backend directory to Python path (we're in backend/tests/utils)
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select  # noqa: E402

from database import AsyncSessionLocal, create_tables  # noqa: E402
from models.chat import ChatSession, ChatStatus  # noqa: E402
from models.plan import Plan, PlanStatus, PlanVersion  # noqa: E402
from models.repository import Repository  # noqa: E402

# Configuration
TEMP_REPOS_DIR = Path(__file__).parent.parent.parent.parent / "temp-repos"
DUMMY_REPOS: List[Dict[str, Any]] = [
    {
        "name": "todo-app-react",
        "description": "A simple React TODO application",
        "files": {
            "package.json": {
                "name": "todo-app-react",
                "version": "1.0.0",
                "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"},
            },
            "src/App.js": """import React, { useState } from 'react';
import './App.css';

function App() {
  const [todos, setTodos] = useState([]);
  const [input, setInput] = useState('');

  const addTodo = () => {
    if (input.trim()) {
      setTodos([...todos, { id: Date.now(), text: input, completed: false }]);
      setInput('');
    }
  };

  const toggleTodo = (id) => {
    setTodos(todos.map(todo =>
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
  };

  return (
    <div className="App">
      <h1>Todo App</h1>
      <div>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && addTodo()}
        />
        <button onClick={addTodo}>Add</button>
      </div>
      <ul>
        {todos.map(todo => (
          <li key={todo.id} style={{textDecoration: todo.completed ? 'line-through' : 'none'}}>
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => toggleTodo(todo.id)}
            />
            {todo.text}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;""",
            "src/App.css": """.App {
  text-align: center;
  margin: 50px auto;
  max-width: 600px;
}

input {
  padding: 10px;
  margin: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

ul {
  list-style: none;
  padding: 0;
}

li {
  padding: 10px;
  border-bottom: 1px solid #eee;
  text-align: left;
}""",
            "README.md": "# Todo App\n\nA simple React todo application for demonstration purposes.",
        },
        "plans": [
            {
                "name": "Add Dark Mode",
                "description": "Implement dark mode toggle for better user experience",
                "target_branch": "main",
                "plan_versions": [
                    {
                        "content": "# Dark Mode Implementation Plan\n\n## Overview\nAdd a dark mode toggle that switches between light and dark themes\n\n## Requirements\n- Toggle button in header\n- Dark theme CSS variables\n- Persist theme preference in localStorage\n\n## Implementation Steps\n1. Create theme context\n2. Add CSS variables for dark/light themes\n3. Implement toggle component\n4. Add localStorage persistence",
                    }
                ],
                "chat_messages": [
                    {
                        "role": "user",
                        "content": "I want to add dark mode to my todo app. Can you help me plan this feature?",
                    },
                    {
                        "role": "assistant",
                        "type": "clarifying_questions",
                        "content": (
                            "1. Do you want the dark mode toggle to be in the header, sidebar, or settings panel?\n"
                            "2. Should the theme preference be saved in localStorage or in a user profile?\n"
                            "3. Are there specific colors or design tokens you'd prefer for the dark theme?\n"
                            "4. Do you need the dark mode to respect the user's system theme preference?\n"
                            "5. Should the transition between themes be instant or animated?"
                        ),
                    },
                    {"role": "user", "content": "Put the toggle in the header and save to localStorage. Use system colors."},
                    {
                        "role": "assistant",
                        "type": "clarifying_questions",
                        "content": (
                            "1. Should the toggle be a simple button, switch, or icon?\n"
                            "2. How should incomplete vs completed todos look different in dark mode?\n"
                            "3. Do you want to support custom themes beyond just light/dark in the future?"
                        ),
                    },
                ],
            },
            {
                "name": "Add User Authentication",
                "description": "Implement user login/logout functionality",
                "target_branch": "feature-auth",
                "plan_versions": [
                    {
                        "content": "# User Authentication Implementation\n\n## Steps\n1. Set up authentication context\n2. Create login/register forms\n3. Implement JWT token handling\n4. Add protected routes\n5. Connect user-specific todos",
                    }
                ],
                "chat_messages": [
                    {
                        "role": "user",
                        "content": ("I need to add user authentication so each user has " "their own todos"),
                    },
                    {
                        "role": "assistant",
                        "type": "clarifying_questions",
                        "content": (
                            "1. Do you want to implement your own auth system or use a service like Auth0/Firebase?\n"
                            "2. What authentication methods do you prefer: email/password, social login, or both?\n"
                            "3. Should users be able to register themselves or will you invite them?\n"
                            "4. Do you need password reset functionality?\n"
                            "5. Should user sessions persist across browser restarts?\n"
                            "6. Do you want to migrate existing todos to a default user or start fresh?"
                        ),
                    },
                ],
            },
        ],
    },
    {
        "name": "python-data-analyzer",
        "description": "A Python data analysis tool with pandas",
        "files": {
            "requirements.txt": "pandas>=1.5.0\nnumpy>=1.21.0\nmatplotlib>=3.5.0\nseaborn>=0.11.0",
            "src/analyzer.py": '''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional

class DataAnalyzer:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df: Optional[pd.DataFrame] = None

    def load_data(self) -> pd.DataFrame:
        """Load data from CSV file"""
        try:
            self.df = pd.read_csv(self.data_path)
            return self.df
        except Exception as e:
            raise ValueError(f"Error loading data: {e}")

    def get_summary_stats(self) -> Dict:
        """Get basic summary statistics"""
        if self.df is None:
            raise ValueError("No data loaded")

        return {
            'shape': self.df.shape,
            'columns': self.df.columns.tolist(),
            'dtypes': self.df.dtypes.to_dict(),
            'null_counts': self.df.isnull().sum().to_dict(),
            'numeric_summary': self.df.describe().to_dict()
        }

    def plot_correlation_matrix(self) -> None:
        """Plot correlation matrix for numeric columns"""
        if self.df is None:
            raise ValueError("No data loaded")

        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            plt.figure(figsize=(10, 8))
            sns.heatmap(self.df[numeric_cols].corr(), annot=True, cmap='coolwarm')
            plt.title('Correlation Matrix')
            plt.tight_layout()
            plt.show()

    def find_outliers(self, column: str) -> pd.DataFrame:
        """Find outliers using IQR method"""
        if self.df is None:
            raise ValueError("No data loaded")

        Q1 = self.df[column].quantile(0.25)
        Q3 = self.df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = self.df[(self.df[column] < lower_bound) | (self.df[column] > upper_bound)]
        return outliers
''',
            "src/__init__.py": "",
            "tests/test_analyzer.py": """import unittest
import pandas as pd
import tempfile
import os
from src.analyzer import DataAnalyzer

class TestDataAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create sample data
        self.test_data = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [2, 4, 6, 8, 10],
            'C': ['a', 'b', 'c', 'd', 'e']
        })

        # Create temporary file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.test_data.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()

        self.analyzer = DataAnalyzer(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_load_data(self):
        df = self.analyzer.load_data()
        self.assertEqual(df.shape, (5, 3))
        self.assertListEqual(df.columns.tolist(), ['A', 'B', 'C'])

    def test_summary_stats(self):
        self.analyzer.load_data()
        stats = self.analyzer.get_summary_stats()
        self.assertEqual(stats['shape'], (5, 3))
        self.assertIn('A', stats['columns'])

if __name__ == '__main__':
    unittest.main()
""",
            "README.md": (
                "# Python Data Analyzer\n\n" "A simple data analysis tool built with pandas for exploring CSV datasets."
            ),
        },
        "plans": [
            {
                "name": "Add Machine Learning Features",
                "description": "Extend analyzer with basic ML capabilities",
                "target_branch": "main",
                "plan_versions": [
                    {
                        "content": "# Machine Learning Integration\n\n## Overview\nAdd basic ML capabilities including clustering, classification, and regression\n\n## Features\n- K-means clustering\n- Linear regression\n- Data preprocessing utilities\n- Model evaluation metrics",
                    }
                ],
                "chat_messages": [
                    {
                        "role": "user",
                        "content": ("Can we add some machine learning capabilities to the " "data analyzer?"),
                    },
                    {
                        "role": "assistant",
                        "type": "clarifying_questions",
                        "content": (
                            "1. What types of ML tasks are you most interested in: classification, regression, clustering, or dimensionality reduction?\n"
                            "2. Do you want supervised learning (with labeled training data) or unsupervised learning capabilities?\n"
                            "3. Should the ML models be pre-trained or trained on the loaded data?\n"
                            "4. Do you need feature engineering tools for data preprocessing?\n"
                            "5. How important is model interpretability vs accuracy for your use case?\n"
                            "6. Would you like automated model selection or manual model configuration?"
                        ),
                    },
                ],
            }
        ],
    },
    {
        "name": "express-api-server",
        "description": "A Node.js Express REST API server",
        "files": {
            "package.json": {
                "name": "express-api-server",
                "version": "1.0.0",
                "main": "server.js",
                "dependencies": {
                    "express": "^4.18.0",
                    "cors": "^2.8.5",
                    "dotenv": "^16.0.0",
                    "mongoose": "^7.0.0",
                },
                "devDependencies": {
                    "nodemon": "^2.0.20",
                    "jest": "^29.0.0",
                },
                "scripts": {
                    "start": "node server.js",
                    "dev": "nodemon server.js",
                    "test": "jest",
                },
            },
            "server.js": """const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// In-memory storage for demo
let users = [
  { id: 1, name: 'John Doe', email: 'john@example.com' },
  { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
];

// Routes
app.get('/', (req, res) => {
  res.json({ message: 'Express API Server is running!' });
});

app.get('/api/users', (req, res) => {
  res.json(users);
});

app.get('/api/users/:id', (req, res) => {
  const user = users.find(u => u.id === parseInt(req.params.id));
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }
  res.json(user);
});

app.post('/api/users', (req, res) => {
  const { name, email } = req.body;
  if (!name || !email) {
    return res.status(400).json({ error: 'Name and email are required' });
  }

  const newUser = {
    id: users.length + 1,
    name,
    email
  };
  users.push(newUser);
  res.status(201).json(newUser);
});

app.put('/api/users/:id', (req, res) => {
  const user = users.find(u => u.id === parseInt(req.params.id));
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  const { name, email } = req.body;
  if (name) user.name = name;
  if (email) user.email = email;

  res.json(user);
});

app.delete('/api/users/:id', (req, res) => {
  const index = users.findIndex(u => u.id === parseInt(req.params.id));
  if (index === -1) {
    return res.status(404).json({ error: 'User not found' });
  }

  users.splice(index, 1);
  res.status(204).send();
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
""",
            ".env": "PORT=3000\nNODE_ENV=development",
            "README.md": "# Express API Server\n\nA simple REST API server built with Express.js for user management.",
        },
        "plans": [
            {
                "name": "Add Database Integration",
                "description": "Replace in-memory storage with MongoDB",
                "target_branch": "feature-database",
                "plan_versions": [
                    {
                        "content": "# MongoDB Integration Plan\n\n## Steps\n1. Set up MongoDB connection\n2. Create User model with Mongoose\n3. Replace in-memory operations with database queries\n4. Add data validation\n5. Implement error handling for database operations\n6. Add database seeding script",
                    }
                ],
                "chat_messages": [
                    {
                        "role": "user",
                        "content": (
                            "I want to replace the in-memory storage with a real " "database. What do you recommend?"
                        ),
                    },
                    {
                        "role": "assistant",
                        "type": "clarifying_questions",
                        "content": (
                            "1. Do you prefer SQL (PostgreSQL, MySQL) or NoSQL (MongoDB, DynamoDB) databases?\n"
                            "2. What's your expected data volume and concurrent user load?\n"
                            "3. Do you need ACID transactions or is eventual consistency acceptable?\n"
                            "4. Are you planning to deploy on cloud services or on-premise?\n"
                            "5. Do you need real-ptime features like subscriptions or change streams?\n"
                            "6. Should the database migration preserve any existing in-memory data structure?"
                        ),
                    },
                ],
            }
        ],
    },
]


def create_git_repo(repo_path: Path) -> None:
    """Initialize a git repository with some commits"""
    os.chdir(repo_path)

    # Initialize git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@codeverse.com"], check=True)
    subprocess.run(["git", "config", "user.name", "CodeVerse Test"], check=True)

    # Add and commit files
    subprocess.run(["git", "add", "."], check=True)
    # Check if there are changes to commit
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if result.returncode != 0:  # There are changes to commit
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

    # Create a feature branch for some repos
    if "auth" in str(repo_path) or "database" in str(repo_path):
        branch_name = "feature-auth" if "auth" in str(repo_path) else "feature-database"
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)

        # Make a small change and commit
        readme_path = repo_path / "README.md"
        with open(readme_path, "a") as f:
            f.write(f"\n\n## Development\n\nCurrently working on {branch_name}")

        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Add development notes for {branch_name}"],
            check=True,
        )
        subprocess.run(["git", "checkout", "main"], check=True)


def create_dummy_repos() -> None:
    """Create dummy git repositories"""
    print(f"Creating dummy repositories in {TEMP_REPOS_DIR}")

    # Create temp-repos directory
    TEMP_REPOS_DIR.mkdir(exist_ok=True)

    for repo_config in DUMMY_REPOS:
        repo_path = TEMP_REPOS_DIR / repo_config["name"]
        print(f"  Creating {repo_config['name']}...")

        # Create directory structure and files
        repo_path.mkdir(exist_ok=True)

        for file_path, content in repo_config["files"].items():
            full_path = repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(content, dict):
                # JSON content
                with open(full_path, "w") as f:
                    json.dump(content, f, indent=2)
            else:
                # Text content
                with open(full_path, "w") as f:
                    f.write(content)

        # Initialize git repository
        original_cwd = os.getcwd()
        try:
            create_git_repo(repo_path)
        finally:
            os.chdir(original_cwd)


async def populate_database() -> None:
    """Populate database with dummy data"""
    print("Populating database with dummy data...")

    # Ensure tables exist
    await create_tables()

    async with AsyncSessionLocal() as session:
        for repo_config in DUMMY_REPOS:
            repo_path = TEMP_REPOS_DIR / repo_config["name"]

            # Create repository
            repository = Repository(
                id=str(uuid.uuid4()),
                name=repo_config["name"],
                path=str(repo_path.absolute()),
                git_url=f"file://{repo_path.absolute()}",
                default_branch="main",
            )
            session.add(repository)
            await session.flush()  # Get the ID

            print(f"  Created repository: {repo_config['name']}")

            # Create plans for this repository
            for plan_config in repo_config.get("plans", []):
                plan_id = str(uuid.uuid4())
                plan = Plan(
                    id=plan_id,
                    repository_id=repository.id,
                    name=plan_config["name"],
                    description=plan_config["description"],
                    target_branch=plan_config["target_branch"],
                    status=PlanStatus.DRAFT.value,
                )
                session.add(plan)
                await session.flush()

                print(f"    Created plan: {plan_config['name']}")

                # Create plan versions
                for plan_version_config in plan_config.get("plan_versions", []):
                    plan_version = PlanVersion(
                        id=str(uuid.uuid4()),
                        plan_id=plan.id,
                        content=plan_version_config["content"],
                        version=1,
                    )
                    session.add(plan_version)

                # Create chat session
                chat_session = ChatSession(
                    id=str(uuid.uuid4()),
                    plan_id=plan.id,
                    messages=plan_config.get("chat_messages", []),
                    status=ChatStatus.ACTIVE.value,
                )
                session.add(chat_session)

                print(f"    Created chat session with {len(plan_config.get('chat_messages', []))} messages")

        await session.commit()
        print("Database populated successfully!")


async def cleanup_database() -> None:
    """Clean up all dummy data from database"""
    print("Cleaning up database...")

    async with AsyncSessionLocal() as session:
        # Get all repositories that point to temp-repos
        result = await session.execute(select(Repository).where(Repository.path.like(f"%{TEMP_REPOS_DIR}%")))
        repositories = result.scalars().all()

        for repo in repositories:
            print(f"  Removing repository: {repo.name}")
            await session.delete(repo)

        await session.commit()
        print("Database cleaned up successfully!")


def cleanup_dummy_repos() -> None:
    """Remove all dummy repositories"""
    if TEMP_REPOS_DIR.exists():
        print(f"Removing dummy repositories from {TEMP_REPOS_DIR}")
        shutil.rmtree(TEMP_REPOS_DIR)
        print("Dummy repositories removed successfully!")
    else:
        print("No dummy repositories to clean up")


async def create_dummy_data() -> None:
    """Create dummy repositories and populate database"""
    create_dummy_repos()
    await populate_database()
    print("\n✅ Dummy data creation completed!")
    print(f"📁 Repositories created in: {TEMP_REPOS_DIR}")
    print("🗄️  Database populated with sample data")


async def cleanup_dummy_data() -> None:
    """Clean up dummy repositories and database entries"""
    await cleanup_database()
    cleanup_dummy_repos()
    print("\n✅ Cleanup completed!")


async def reset_dummy_data() -> None:
    """Clean up and recreate all dummy data"""
    print("🔄 Resetting dummy data...")
    await cleanup_dummy_data()
    await create_dummy_data()


async def main():
    parser = argparse.ArgumentParser(description="Manage dummy data for CodeVerse")
    parser.add_argument(
        "action",
        choices=["create", "cleanup", "reset"],
        help=("Action to perform: create dummy data, cleanup, or reset " "(cleanup + create)"),
    )

    args = parser.parse_args()

    try:
        if args.action == "create":
            await create_dummy_data()
        elif args.action == "cleanup":
            await cleanup_dummy_data()
        elif args.action == "reset":
            await reset_dummy_data()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
