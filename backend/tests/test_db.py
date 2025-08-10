"""
Test database setup and basic operations
"""
import asyncio
import os
import sys

import pytest

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import AsyncSessionLocal, create_tables, drop_tables
from models import ChatSession, Plan, PlanVersion, Repository
from models.chat import ChatStatus
from models.plan import PlanStatus


@pytest.mark.asyncio
async def test_database():
    """Test database operations"""
    print("Testing database operations...")

    try:
        # Setup database
        await drop_tables()
        await create_tables()
        print("✓ Database tables created successfully")

        # Test basic CRUD operations
        async with AsyncSessionLocal() as session:
            # Create a repository
            repo = Repository(
                name="test-repo",
                path="/path/to/repo",
                git_url="https://github.com/user/repo.git",
                default_branch="main",
            )
            session.add(repo)
            await session.commit()
            await session.refresh(repo)
            print(f"✓ Created repository: {repo}")

            # Create a plan
            plan = Plan(
                repository_id=repo.id,
                name="test-feature",
                description="A test feature plan",
                target_branch="feature/test",
                status=PlanStatus.DRAFT.value,  # Use .value for string
            )
            session.add(plan)
            await session.commit()
            await session.refresh(plan)
            print(f"✓ Created plan: {plan}")

            # Create a plan artifact
            artifact = PlanVersion(
                plan_id=plan.id,
                content={"steps": ["Step 1", "Step 2", "Step 3"]},
                version=1,
            )
            session.add(artifact)
            await session.commit()
            await session.refresh(artifact)
            print(f"✓ Created plan artifact: {artifact}")

            # Create a chat session
            chat = ChatSession(
                plan_id=plan.id,
                messages=[
                    {"role": "user", "content": "Hello"},
                    {
                        "role": "assistant",
                        "content": "Hi! How can I help with your feature planning?",
                    },
                ],
                status=ChatStatus.ACTIVE.value,  # Use .value for string
            )
            session.add(chat)
            await session.commit()
            await session.refresh(chat)
            print(f"✓ Created chat session: {chat}")

            print("\n✅ All database tests passed successfully!")

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        pytest.fail(f"Database test failed: {e}")


if __name__ == "__main__":
    success = asyncio.run(test_database())
    sys.exit(0 if success else 1)
