"""
claude_service.py

Provides an async generator API to stream only the final result content from
Claude Code, suitable for consumption by other modules.
"""

from __future__ import annotations

import sys
from typing import AsyncGenerator, Optional

try:
    from claude_code_sdk import (
        ClaudeCodeOptions,
        query,
    )
except Exception:  # pragma: no cover
    print(
        "Error: Failed to import 'claude_code_sdk'.\nInstall it with: pip install claude-code-sdk",
        file=sys.stderr,
    )
    raise


SYSTEM_PROMPT = """
You are **Claude Code**, an AI agent assistant specialized in helping developers draft high-quality implementation plans. Given the user's raw notes below, your output must include two sections:

---

## 1. **Plan Draft** (in Markdown)
- Produce a clear, organized outline breaking down the development into modules or tasks.
- Include structure, key steps, dependencies, technology stack, code architecture, and testing strategy.
- Use a **plan-and-solve** approach: first outline the overall plan, then optionally detail sub-steps.

## 2. **Clarifying Questions**
- List any important missing information that would impact the plan's accuracy.
- Focus on user experience, feature edge cases, data inputs/outputs, integration requirements, constraints, or any ambiguity.

**Instructions:**
1. Provide a transparent, simple plan first, then details.
2. Avoid assumptions—list uncertainties in clarifying questions.
3. No more than 8 clarifying questions so choose the best ones.
4. Treat this as a *draft* to be reviewed and improved collaboratively with the user.
5. Do not use emojis in your response!
"""


async def _query_claude_stream(
    working_directory: str,
    system_prompt: Optional[str],
    prompt: str,
) -> AsyncGenerator[str, None]:
    """Yield only final-result stream chunks from Claude Code.

    - Emits deltas if available, otherwise a single final result string.
    - Ignores intermediate thinking/assistant/user/system messages.
    - Prints SDK-reported errors to stderr without yielding them.
    """
    saw_any_delta = False
    async for message in query(
        prompt=prompt,
        options=ClaudeCodeOptions(
            cwd=working_directory,
            system_prompt=system_prompt,
        ),
    ):
        message_type_name = type(message).__name__

        if message_type_name == "ErrorMessage":
            err_text = getattr(message, "error", None)
            if err_text:
                print(f"Error: {err_text}", file=sys.stderr, flush=True)
            continue

        if message_type_name == "ResultMessage":
            delta_text = getattr(message, "delta", None) or getattr(message, "result_delta", None)
            if delta_text:
                saw_any_delta = True
                yield delta_text
                continue

            result_text = getattr(message, "result", None)
            if result_text and not saw_any_delta:
                yield result_text


async def generate_plan(
    project_dir: str,
    user_raw_notes: str,
    prev_clarfying_questions: Optional[str],
    current_plan: Optional[str],
) -> AsyncGenerator[str, None]:
    """Stream a plan for the given project based on raw notes.

    The stream includes only final result content (no thinking messages).
    """
    async for chunk in _query_claude_stream(
        working_directory=project_dir,
        system_prompt=SYSTEM_PROMPT,
        prompt=user_raw_notes,
    ):
        yield chunk


