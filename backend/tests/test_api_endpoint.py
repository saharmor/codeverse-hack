#!/usr/bin/env python3
"""
Test script for the generate_plan_endpoint API

This script demonstrates how to test the API endpoint with different scenarios.
"""

import asyncio
import json
from typing import Optional

import aiohttp

# Configuration
BASE_URL = "http://localhost:8000"
API_ENDPOINT = "/api/business/plans"

# Test data scenarios
TEST_SCENARIOS = [
    {
        "name": "Simple Feature Request",
        "user_message": "I want to add user authentication to my app with login and registration forms",
        "description": "Basic user auth feature request",
    },
    {
        "name": "Complex Feature with Context",
        "user_message": "Build a real-time chat system with WebSocket support, message history, and file uploads",
        "plan_artifact": {"previous_version": "v1.0", "status": "draft"},
        "description": "Complex feature with existing context",
    },
    {
        "name": "Refinement Request",
        "user_message": "Actually, let's also add emoji reactions to messages and typing indicators",
        "chat_messages": [
            {"role": "user", "content": "Build a chat system", "timestamp": "2024-01-01T12:00:00Z"},
            {
                "role": "assistant",
                "content": "I'll help you build a chat system...",
                "timestamp": "2024-01-01T12:01:00Z",
            },
        ],
        "description": "Follow-up refinement request",
    },
]


class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_server(self) -> bool:
        """Check if the server is running"""
        if not self.session:
            return False
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    print("✅ Server is running")
                    return True
                else:
                    print(f"❌ Server responded with status: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("Please make sure the backend is running on http://localhost:8000")
            return False

    async def get_test_plan_id(self) -> Optional[str]:
        """Get a plan ID from the database for testing"""
        if not self.session:
            return None
        try:
            # First get repositories
            async with self.session.get(f"{self.base_url}/api/repositories") as response:
                if response.status == 200:
                    repositories = await response.json()
                    if repositories:
                        repo_id = repositories[0]["id"]
                        print(f"🗂️  Using repository: {repositories[0]['name']} ({repo_id})")

                        # Then get plans for this repository
                        async with self.session.get(
                            f"{self.base_url}/api/repositories/{repo_id}/plans"
                        ) as plans_response:
                            if plans_response.status == 200:
                                plans = await plans_response.json()
                                if plans:
                                    plan_id = plans[0]["id"]
                                    print(f"📋 Using existing plan: {plans[0]['name']} ({plan_id})")
                                    return plan_id
        except Exception as e:
            print(f"Error fetching plans: {e}")
            pass

        # If no plans exist, we need to create dummy data
        print("⚠️  No plans found. You need to create dummy data first.")
        print("Run: ./scripts/db.sh create")
        return None

    async def stream_plan_generation(self, plan_id: str, request_data: dict) -> None:
        """Test the streaming plan generation endpoint"""
        if not self.session:
            print("❌ No session available")
            return

        url = f"{self.base_url}{API_ENDPOINT}/{plan_id}/generate"

        print(f"🚀 Testing: {url}")
        print(f"📝 Request data: {json.dumps(request_data, indent=2)}")
        print("=" * 50)

        try:
            async with self.session.post(url, json=request_data, headers={"Accept": "text/event-stream"}) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ Error {response.status}: {error_text}")
                    return

                print("📡 Streaming response:")
                print("-" * 30)

                chunk_count = 0
                async for line_bytes in response.content:
                    line = line_bytes.decode("utf-8").strip()

                    if line.startswith("data: "):
                        chunk_count += 1
                        try:
                            data = json.loads(line[6:])  # Remove 'data: ' prefix

                            if data.get("type") == "complete":
                                print(f"\n✅ Stream completed ({chunk_count} chunks received)")
                                break
                            elif data.get("type") == "error":
                                print(f"\n❌ Error: {data.get('message')}")
                                break
                            elif "chunk" in data:
                                output_type = data.get("output_type", "unknown")
                                chunk_content = data["chunk"]
                                print(f"[{output_type}] {chunk_content}", end="", flush=True)
                        except json.JSONDecodeError:
                            print(f"\n⚠️  Invalid JSON in chunk: {line}")

                print("\n" + "=" * 50)

        except Exception as e:
            print(f"❌ Request failed: {e}")

    async def run_tests(self):
        """Run all test scenarios"""
        print("🧪 CodeVerse API Endpoint Tester")
        print("=" * 50)

        # Check server
        if not await self.check_server():
            return

        # Get a plan ID for testing
        plan_id = await self.get_test_plan_id()
        if not plan_id:
            return

        # Run test scenarios
        for i, scenario in enumerate(TEST_SCENARIOS, 1):
            print(f"\n🔄 Test {i}/3: {scenario['name']}")
            print(f"📄 {scenario['description']}")

            # Prepare request data
            request_data = {"user_message": scenario["user_message"]}
            if "plan_artifact" in scenario:
                request_data["plan_artifact"] = scenario["plan_artifact"]
            if "chat_messages" in scenario:
                request_data["chat_messages"] = scenario["chat_messages"]

            await self.stream_plan_generation(plan_id, request_data)

            if i < len(TEST_SCENARIOS):
                input("\n⏸️  Press Enter to continue to next test...")


async def main():
    async with APITester() as tester:
        await tester.run_tests()


if __name__ == "__main__":
    print("Starting API endpoint test...")
    asyncio.run(main())
