"""
Database setup script for development
"""
import asyncio
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, drop_tables
from models import Repository, Plan, PlanArtifact, ChatSession

async def setup_database():
    """Create all tables in the database"""
    print("Setting up database...")
    
    try:
        # Drop existing tables (for development)
        print("Dropping existing tables...")
        await drop_tables()
        
        # Create all tables
        print("Creating tables...")
        await create_tables()
        
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = asyncio.run(setup_database())
    sys.exit(0 if success else 1)