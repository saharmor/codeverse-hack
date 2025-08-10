#!/usr/bin/env python3
"""
API endpoint testing script
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    print("Testing CodeVerse API endpoints...")
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✅ Health check passed")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False
    
    # Create repository
    print("\n2. Testing repository creation...")
    repo_data = {
        "name": "codeverse-app",
        "path": "/Users/galw/Git/innovation/codeverse-hack",
        "git_url": "https://github.com/user/codeverse-app.git"
    }
    response = requests.post(f"{BASE_URL}/api/repositories", json=repo_data)
    if response.status_code == 200:
        print("✅ Repository created successfully")
        repo = response.json()
        repo_id = repo["id"]
        print(f"Repository ID: {repo_id}")
        print(json.dumps(repo, indent=2))
    else:
        print(f"❌ Repository creation failed: {response.status_code}")
        print(response.text)
        return False
    
    # Get all repositories
    print("\n3. Testing get repositories...")
    response = requests.get(f"{BASE_URL}/api/repositories")
    if response.status_code == 200:
        print("✅ Get repositories successful")
        repos = response.json()
        print(f"Found {len(repos)} repositories")
    else:
        print(f"❌ Get repositories failed: {response.status_code}")
        return False
    
    # Create plan
    print("\n4. Testing plan creation...")
    plan_data = {
        "repository_id": repo_id,
        "name": "authentication-feature",
        "description": "Add user authentication to the app",
        "target_branch": "feature/auth",
        "version": 1,
        "status": "draft"
    }
    response = requests.post(f"{BASE_URL}/api/repositories/{repo_id}/plans", json=plan_data)
    if response.status_code == 200:
        print("✅ Plan created successfully")
        plan = response.json()
        plan_id = plan["id"]
        print(f"Plan ID: {plan_id}")
        print(json.dumps(plan, indent=2))
    else:
        print(f"❌ Plan creation failed: {response.status_code}")
        print(response.text)
        return False
    
    # Get plans for repository
    print("\n5. Testing get plans for repository...")
    response = requests.get(f"{BASE_URL}/api/repositories/{repo_id}/plans")
    if response.status_code == 200:
        print("✅ Get plans successful")
        plans = response.json()
        print(f"Found {len(plans)} plans for repository")
    else:
        print(f"❌ Get plans failed: {response.status_code}")
        return False
    
    # Create plan artifact
    print("\n6. Testing plan artifact creation...")
    artifact_data = {
        "plan_id": plan_id,
        "content": {
            "steps": [
                "Research authentication libraries",
                "Design user model",
                "Implement login/logout endpoints",
                "Add password hashing",
                "Create frontend login form"
            ],
            "estimated_time": "5 days",
            "dependencies": ["database", "frontend framework"]
        },
        "artifact_type": "feature_plan"
    }
    response = requests.post(f"{BASE_URL}/api/plans/{plan_id}/artifacts", json=artifact_data)
    if response.status_code == 200:
        print("✅ Plan artifact created successfully")
        artifact = response.json()
        artifact_id = artifact["id"]
        print(f"Artifact ID: {artifact_id}")
        print(json.dumps(artifact, indent=2))
    else:
        print(f"❌ Plan artifact creation failed: {response.status_code}")
        print(response.text)
        return False
    
    # Create chat session
    print("\n7. Testing chat session creation...")
    chat_data = {
        "plan_id": plan_id,
        "messages": [
            {"role": "user", "content": "I need help implementing authentication"},
            {"role": "assistant", "content": "I can help you with that! Let's start by choosing an authentication strategy."}
        ],
        "status": "active"
    }
    response = requests.post(f"{BASE_URL}/api/plans/{plan_id}/chat", json=chat_data)
    if response.status_code == 200:
        print("✅ Chat session created successfully")
        chat = response.json()
        chat_id = chat["id"]
        print(f"Chat ID: {chat_id}")
        print(json.dumps(chat, indent=2))
    else:
        print(f"❌ Chat session creation failed: {response.status_code}")
        print(response.text)
        return False
    
    print("\n🎉 All API tests passed successfully!")
    print(f"""
Summary:
- Repository ID: {repo_id}
- Plan ID: {plan_id}
- Artifact ID: {artifact_id}
- Chat ID: {chat_id}
""")
    return True

if __name__ == "__main__":
    # Wait a moment for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    try:
        success = test_api_endpoints()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
        exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        exit(1)