"""
Claude Code integration service for plan generation.
"""
import asyncio
import json
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from models import Plan, Repository


async def generate_plan(plan_context: Dict[str, Any]) -> AsyncIterator[str]:
    """
    Core function that orchestrates plan generation with Claude Code.

    Args:
        plan_context: Dictionary containing:
            - plan: Plan model instance
            - repository: Repository model instance
            - existing_artifact: Current plan artifact (if any)
            - chat_history: Previous conversation messages
            - user_message: Latest user input

    Yields:
        Streaming response from Claude Code
    """

    plan: Plan = plan_context["plan"]
    repository: Repository = plan_context["repository"]
    existing_artifact = plan_context.get("existing_artifact")
    chat_history = plan_context.get("chat_history", [])
    user_message = plan_context["user_message"]

    # Build the prompt for Claude Code
    prompt = _build_claude_prompt(
        plan=plan,
        repository=repository,
        existing_artifact=existing_artifact,
        chat_history=chat_history,
        user_message=user_message,
    )

    # Call Claude Code CLI with the prompt
    try:
        async for chunk in _call_claude_code(prompt, str(repository.path)):
            yield chunk
    except Exception as e:
        raise Exception(f"Claude Code generation failed: {str(e)}")


def _build_claude_prompt(
    plan: Plan,
    repository: Repository,
    existing_artifact: Optional[Dict[str, Any]],
    chat_history: List[Dict[str, Any]],
    user_message: str,
) -> str:
    """
    Build a comprehensive prompt for Claude Code based on the plan context.
    """

    prompt_parts = [
        f"# Code Planning Session for {plan.name}",
        "",
        "## Project Context",
        f"Repository: {repository.name}",
        f"Path: {repository.path}",
        f"Target Branch: {plan.target_branch}",
        f"Plan Description: {plan.description or 'No description provided'}",
        "",
    ]

    # Add existing plan artifact if available
    if existing_artifact:
        prompt_parts.extend(["## Current Plan Artifact", "```json", json.dumps(existing_artifact, indent=2), "```", ""])

    # Add chat history context
    if chat_history:
        prompt_parts.extend(["## Previous Conversation", ""])

        # Show last few messages for context
        recent_messages = chat_history[-5:] if len(chat_history) > 5 else chat_history
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            prompt_parts.append(f"**{role.title()}:** {content}")
            prompt_parts.append("")

    # Add the current user message
    prompt_parts.extend(
        [
            "## Current Request",
            f"**User:** {user_message}",
            "",
            "## Instructions",
            "You are helping with code planning for this project. Based on the above context:",
            "1. If this is an initial plan, create a comprehensive feature plan",
            "2. If updating an existing plan, refine it based on the user's feedback",
            "3. If the user is asking clarifying questions, provide detailed answers",
            "4. Always consider the codebase context and existing patterns",
            "",
            "Please provide your response as a structured plan with clear implementation steps.",
            "Focus on being practical and actionable for the development team.",
        ]
    )

    return "\n".join(prompt_parts)


async def _call_claude_code(prompt: str, repo_path: str) -> AsyncIterator[str]:
    """
    Call Claude Code CLI and stream the response.

    Args:
        prompt: The prompt to send to Claude Code
        repo_path: Path to the repository for context

    Yields:
        Streaming chunks from Claude Code
    """

    # Change to repository directory for context
    original_cwd = Path.cwd()

    try:
        # Start Claude Code process
        cmd = ["claude", "code", prompt]

        # Create the subprocess with streaming output
        process = await asyncio.create_subprocess_exec(
            *cmd, cwd=repo_path, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        # Stream output as it becomes available
        if process.stdout is not None:
            while True:
                try:
                    # Read from stdout with timeout
                    line_bytes = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
                    if not line_bytes:
                        break
                    line = line_bytes.decode("utf-8").rstrip()
                    if line:  # Only yield non-empty lines
                        yield line

                except asyncio.TimeoutError:
                    # Check if process is still running
                    if process.returncode is not None:
                        break
                    continue

        # Wait for process to complete and check return code
        await process.wait()

        if process.returncode != 0:
            error_output = ""
            if process.stderr:
                error_bytes = await process.stderr.read()
                error_output = error_bytes.decode("utf-8") if error_bytes else ""
            raise Exception(f"Claude Code exited with code {process.returncode}: {error_output}")

    except FileNotFoundError:
        # Fallback: simulate Claude response if Claude CLI is not available
        yield "⚠️ Claude Code CLI not found. Using mock response for development."
        yield ""
        yield "## Updated Plan"
        yield ""
        yield f"Based on your request: '{prompt[-100:]}...'"
        yield ""
        yield "### Implementation Steps"
        yield "1. Review existing codebase patterns"
        yield "2. Design the solution architecture"
        yield "3. Implement core functionality"
        yield "4. Add tests and documentation"
        yield "5. Review and refactor as needed"
        yield ""
        yield "### Next Questions"
        yield "- What specific technologies should we use?"
        yield "- Are there any performance requirements?"
        yield "- Should we follow any particular design patterns?"

    except Exception as e:
        raise Exception(f"Failed to execute Claude Code: {str(e)}")

    finally:
        # Restore original directory
        if original_cwd != Path.cwd():
            import os

            os.chdir(original_cwd)
