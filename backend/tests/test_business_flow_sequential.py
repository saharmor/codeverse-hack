"""
Sequential test for the complete business logic flow.

This test covers:
1. Repository creation
2. Plan creation in repository
3. Business logic endpoint with Claude Code integration
"""
import asyncio
import json
import uuid

import httpx
import pytest


class TestBusinessFlowSequential:
    """Sequential test class that maintains state between test steps."""

    # Class variables to maintain state
    repository_id: str = ""
    plan_id: str = ""
    base_url = "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_01_create_repository(self):
        """Step 1: Create a repository."""
        # Use unique path for each test run to avoid constraint violations
        unique_id = str(uuid.uuid4())[:8]
        repository_path = f"../../test-repos/test-codeverse-{unique_id}"

        # Create the directory structure for testing
        import os

        os.makedirs(repository_path, exist_ok=True)

        # Create a basic README file to make it look like a real repo
        with open(f"{repository_path}/README.md", "w") as f:
            f.write("# Test CodeVerse App\n\nThis is a test repository for mobile chat application development.\n")

        repository_data = {
            "name": f"test-codeverse-app-{unique_id}",
            "path": repository_path,
            "git_url": "https://github.com/example/test-codeverse-app.git",
            "default_branch": "main",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/api/repositories", json=repository_data)

        if response.status_code != 200:
            print(f"❌ Repository creation failed with status {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 200
        repo_response = response.json()

        # Store repository ID for next tests
        TestBusinessFlowSequential.repository_id = str(repo_response["id"])

        print(f"✅ Repository created successfully with ID: {self.repository_id}")
        assert repo_response["name"] == repository_data["name"]
        assert repo_response["path"] == repository_data["path"]
        assert repo_response["default_branch"] == repository_data["default_branch"]

    @pytest.mark.asyncio
    async def test_02_create_plan(self):
        """Step 2: Create a plan in the repository."""
        plan_data = {
            "name": "Mobile Chat App Design",
            "description": "Design and plan a mobile chat application with real-time messaging",
            "target_branch": "main",
            "repository_id": self.repository_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/api/repositories/{self.repository_id}/plans", json=plan_data)

        if response.status_code != 200:
            print(f"❌ Plan creation failed with status {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 200
        plan_response = response.json()

        # Store plan ID for next test
        TestBusinessFlowSequential.plan_id = str(plan_response["id"])

        print(f"✅ Plan created successfully with ID: {self.plan_id}")
        assert plan_response["name"] == plan_data["name"]
        assert plan_response["description"] == plan_data["description"]
        assert plan_response["target_branch"] == plan_data["target_branch"]
        assert str(plan_response["repository_id"]) == self.repository_id

    @pytest.mark.asyncio
    async def test_03_business_logic_initial_request(self):
        """Step 3: Test the main business logic with initial app design request."""
        initial_request = {
            "user_message": (
                "I want to build a modern mobile chat application similar to WhatsApp. "
                "The app should have real-time messaging, group chats, media sharing, "
                "and user authentication. I'm thinking of using React Native for the frontend "
                "and Node.js with Socket.io for the backend. Can you help me create a "
                "comprehensive plan with architecture decisions and implementation steps?"
            ),
            "existing_artifact": None,
            "chat_history": [],
        }

        print(f"🚀 Calling business logic endpoint for plan {self.plan_id}...")
        print(f"📝 User message: {initial_request['user_message'][:100]}...")

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Make streaming request
            async with client.stream(
                "POST",
                f"{self.base_url}/api/business/plans/{self.plan_id}/generate",
                json=initial_request,
                headers={"Accept": "text/event-stream"},
            ) as response:
                assert response.status_code == 200

                # Debug response headers
                print(f"📋 Response headers: {dict(response.headers)}")
                actual_content_type = response.headers.get("content-type", "")
                print(f"📋 Actual content-type: '{actual_content_type}'")

                if "text/event-stream" not in actual_content_type:
                    print(f"⚠️  Expected 'text/event-stream' but got '{actual_content_type}'")

                assert "text/event-stream" in actual_content_type

                print("📡 Receiving streaming response from Claude Code...")

                chunks_received = 0
                full_response = []

                async for chunk in response.aiter_text():
                    if chunk.strip():
                        chunks_received += 1

                        # Parse Server-Sent Events format
                        if chunk.startswith("data: "):
                            try:
                                data_json = json.loads(chunk[6:])  # Remove "data: " prefix
                                chunk_type = data_json.get("type")
                                content = data_json.get("content", "")

                                if chunk_type == "chunk" and content:
                                    full_response.append(content)
                                    print(f"📄 Chunk {chunks_received}: {content[:80]}...")

                                elif chunk_type == "complete":
                                    print("✅ Stream completed successfully")
                                    break

                                elif chunk_type == "error":
                                    error_msg = data_json.get("message", data_json.get("error", "Unknown error"))
                                    print(f"❌ Error received: {error_msg}")
                                    pytest.fail(f"Business logic returned error: {error_msg}")

                            except json.JSONDecodeError:
                                # Handle non-JSON chunks (might be raw text)
                                if chunk.strip():
                                    full_response.append(chunk.strip())
                                    print(f"📄 Text chunk {chunks_received}: {chunk.strip()[:80]}...")

                # Validate response
                assert chunks_received > 0, "No chunks received from business logic endpoint"

                combined_response = "\n".join(full_response)
                print(f"\n📋 Full response received ({len(combined_response)} characters)")
                print("=" * 50)
                print(combined_response[:500] + "..." if len(combined_response) > 500 else combined_response)
                print("=" * 50)

                # Validate content contains expected elements
                response_lower = combined_response.lower()

                # Should contain planning-related keywords
                assert any(
                    keyword in response_lower
                    for keyword in ["plan", "architecture", "implementation", "steps", "mobile", "chat"]
                ), "Response doesn't seem to contain planning content"

                # Should contain some technical elements
                assert any(
                    tech in response_lower
                    for tech in ["react", "node", "socket", "api", "database", "frontend", "backend"]
                ), "Response doesn't contain expected technical terms"

                print("✅ Business logic test completed successfully!")
                print(f"📊 Received {chunks_received} chunks with {len(combined_response)} total characters")

    @pytest.mark.asyncio
    async def test_04_cleanup(self):
        """Step 4: Clean up test data."""
        print("🧹 Cleaning up test data...")

        # Get repository path before deleting from database
        async with httpx.AsyncClient() as client:
            repo_get_response = await client.get(f"{self.base_url}/api/repositories/{self.repository_id}")
            if repo_get_response.status_code == 200:
                repo_data = repo_get_response.json()
                repo_path = repo_data.get("path")

                # Delete temporary directory
                if repo_path and repo_path.startswith("/tmp/test-repos/"):
                    import os
                    import shutil

                    if os.path.exists(repo_path):
                        shutil.rmtree(repo_path)
                        print(f"✅ Temporary directory {repo_path} cleaned up")

            # Delete plan
            plan_response = await client.delete(f"{self.base_url}/api/plans/{self.plan_id}")
            assert plan_response.status_code == 200
            print(f"✅ Plan {self.plan_id} deleted")

            # Delete repository
            repo_response = await client.delete(f"{self.base_url}/api/repositories/{self.repository_id}")
            assert repo_response.status_code == 200
            print(f"✅ Repository {self.repository_id} deleted")

        print("🎉 All cleanup completed successfully!")


if __name__ == "__main__":
    # Run the test manually for debugging
    async def run_manual_test():
        test_instance = TestBusinessFlowSequential()

        print("🎯 Starting Sequential Business Logic Test")
        print("=" * 60)

        try:
            await test_instance.test_01_create_repository()
            await test_instance.test_02_create_plan()
            await test_instance.test_03_business_logic_initial_request()
            await test_instance.test_04_cleanup()

            print("\n🏆 ALL TESTS PASSED SUCCESSFULLY!")

        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            # Try cleanup even if tests failed
            try:
                await test_instance.test_04_cleanup()
            except Exception as e:
                print(f"❌ Cleanup failed: {str(e)}")
                pass
            raise

    # Run the manual test
    asyncio.run(run_manual_test())
