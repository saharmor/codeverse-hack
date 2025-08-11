#!/usr/bin/env python3
"""
Test script for the business logic API endpoint
"""
import json

import pytest
import requests

BASE_URL = "http://localhost:8000"


def test_plan_generation():
    """Test the business logic plan generation endpoint"""
    print("Testing CodeVerse Business Logic API...")

    # First, create the test data like in the main test

    # Create repository
    print("\n1. Creating repository...")
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    repo_path = f"/tmp/test-repos/test-business-{unique_id}"

    # Create the directory structure for testing
    import os

    os.makedirs(repo_path, exist_ok=True)

    # Create a basic README file to make it look like a real repo
    with open(f"{repo_path}/README.md", "w") as f:
        f.write("# Test Business Repository\n\nThis is a test repository for AI integration testing.\n")

    repo_data = {
        "name": f"test-business-repo-{unique_id}",
        "path": repo_path,
        "git_url": f"https://github.com/user/test-business-repo-{unique_id}.git",
    }
    response = requests.post(f"{BASE_URL}/api/repositories", json=repo_data)
    if response.status_code != 200:
        print(f"❌ Repository creation failed: {response.status_code}")
        print(response.text)
        pytest.fail("Request failed")

    repo = response.json()
    repo_id = repo["id"]
    print(f"✅ Repository created: {repo_id}")

    # Create plan
    print("\n2. Creating plan...")
    plan_data = {
        "repository_id": repo_id,
        "name": "ai-integration-feature",
        "description": "Add AI-powered code analysis to the platform",
        "target_branch": "feature/ai-integration",
        "version": 1,
        "status": "draft",
    }
    response = requests.post(f"{BASE_URL}/api/repositories/{repo_id}/plans", json=plan_data)
    if response.status_code != 200:
        print(f"❌ Plan creation failed: {response.status_code}")
        print(response.text)
        pytest.fail("Request failed")

    plan = response.json()
    plan_id = plan["id"]
    print(f"✅ Plan created: {plan_id}")

    # Create initial plan version (optional)
    print("\n3. Creating initial plan version...")
    version_data = {
        "plan_id": plan_id,
        "content": (
            "# AI Integration Plan\n\n## Overview\nInitial plan for AI integration\n\n## Goals\n"
            "- Integrate Claude API for code analysis\n- Create streaming response system\n"
            "- Build user interface for AI interactions\n\n## Status\ndraft"
        ),
        "version": 1,
    }
    response = requests.post(f"{BASE_URL}/api/plans/{plan_id}/plan_versions", json=version_data)
    if response.status_code != 200:
        print(f"❌ Version creation failed: {response.status_code}")
        print(response.text)
        pytest.fail("Request failed")

    version = response.json()
    print(f"✅ Version created: {version['id']}")

    # Create chat session
    print("\n4. Creating chat session...")
    chat_data = {
        "plan_id": plan_id,
        "messages": [
            {"role": "user", "content": "I want to integrate AI code analysis. What's the best approach?"},
            {
                "role": "assistant",
                "content": (
                    "Great question! I'd recommend starting with API design and then "
                    "implementing the streaming response system."
                ),
            },
        ],
        "status": "active",
    }
    response = requests.post(f"{BASE_URL}/api/plans/{plan_id}/chat", json=chat_data)
    if response.status_code != 200:
        print(f"❌ Chat creation failed: {response.status_code}")
        print(response.text)
        pytest.fail("Request failed")

    chat = response.json()
    print(f"✅ Chat created: {chat['id']}")

    # Now test the business logic endpoint
    print("\n5. Testing plan generation endpoint...")

    generation_request = {
        "user_message": (
            "How should I structure the API endpoints for the AI integration? "
            "I need streaming responses and proper error handling."
        ),
        "plan_artifact": (
            "Updated plan with specific API requirements\n\n## Requirements\n"
            "- Streaming API responses\n- Error handling and retries\n"
            "- Authentication for AI services\n- Rate limiting and quota management\n\n"
            "## Architecture\nFastAPI + WebSockets + Claude API"
        ),
        "chat_messages": [
            {"role": "user", "content": "I want to integrate AI code analysis. What's the best approach?"},
            {
                "role": "assistant",
                "content": (
                    "Great question! I'd recommend starting with API design and then "
                    "implementing the streaming response system."
                ),
            },
            {"role": "user", "content": "How should I structure the API endpoints for the AI integration?"},
        ],
    }

    # Use streaming request
    try:
        response = requests.post(
            f"{BASE_URL}/api/business/plans/{plan_id}/generate", json=generation_request, stream=True, timeout=30
        )

        if response.status_code != 200:
            print(f"❌ Plan generation failed: {response.status_code}")
            print(response.text)
            pytest.fail("Request failed")

        print("✅ Plan generation started, streaming response:")
        print("-" * 50)

        # Process streaming response
        chunk_count = 0
        for line in response.iter_lines():
            if line:
                try:
                    # Skip empty lines and "data: " prefix if present
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]  # Remove "data: " prefix

                    if line_str.strip():
                        try:
                            data = json.loads(line_str)
                            # Handle streaming chunk data
                            if data.get("chunk") and data.get("output_type"):
                                print(data["chunk"], end="", flush=True)
                                chunk_count += 1
                            # Handle completion/error signals
                            elif data.get("type") == "complete":
                                print("\n" + "-" * 50)
                                print(f"✅ Plan generation completed ({chunk_count} chunks received)")
                                break
                            elif data.get("type") == "error":
                                print(f"\n❌ Error during generation: {data['message']}")
                                pytest.fail("Request failed")
                        except json.JSONDecodeError:
                            # If it's not JSON, treat as plain text
                            print(line_str, end="", flush=True)
                            chunk_count += 1
                except Exception as e:
                    print(f"Error processing chunk: {e}")
                    continue

        if chunk_count == 0:
            print("⚠️  No chunks received - this might indicate an issue")
            pytest.fail("Request failed")

        print("\n✅ Business logic endpoint test completed successfully!")
        print(f"Generated response with {chunk_count} chunks")

    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        pytest.fail("Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        pytest.fail(f"Request failed: {e}")


if __name__ == "__main__":
    import time

    print("Waiting for server to be ready...")
    time.sleep(2)

    try:
        success = test_plan_generation()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
        exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        exit(1)
