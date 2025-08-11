"""
claude_service.py

Provides an async generator API to stream only the final result content from
Claude Code, suitable for consumption by other modules.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import AsyncGenerator, Dict, List, Optional, Tuple

try:
    from claude_code_sdk import ClaudeCodeOptions, query
except Exception:  # pragma: no cover
    print(
        "Error: Failed to import 'claude_code_sdk'.\nInstall it with: pip install claude-code-sdk",
        file=sys.stderr,
    )
    raise

from config import settings

# Import prompt generation utilities
from .claude_prompts import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_NON_FIRST_ITERATION,
    ClaudeOutputManager,
    ClaudeOutputType,
    build_vocab_prompt,
)

logger = logging.getLogger("codeverse.claude")


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
    # Ensure Claude CLI is in PATH - try common locations
    claude_paths = [
        os.path.expanduser("~/.claude/local"),  # Official Claude CLI location
        "/usr/local/bin",  # Common system-wide install location
        os.path.expanduser("~/node_modules/.bin"),  # npm local install
    ]

    current_path = os.environ.get("PATH", "")

    for claude_path in claude_paths:
        if os.path.exists(claude_path) and claude_path not in current_path:
            os.environ["PATH"] = f"{claude_path}:{current_path}"
            current_path = os.environ["PATH"]  # Update for next iteration

    # Also check if CLAUDE_CLI_PATH environment variable is set
    custom_claude_path = os.environ.get("CLAUDE_CLI_PATH")
    if custom_claude_path and os.path.exists(custom_claude_path) and custom_claude_path not in current_path:
        os.environ["PATH"] = f"{custom_claude_path}:{current_path}"
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
                if settings.DEBUG:
                    logger.error("claude.error cwd=%s err=%s", working_directory, err_text)
            continue

        if message_type_name == "ResultMessage":
            delta_text = getattr(message, "delta", None) or getattr(message, "result_delta", None)
            if delta_text:
                if settings.DEBUG:
                    logger.debug("claude.delta size=%d", len(delta_text))
                saw_any_delta = True
                yield delta_text
                continue

            result_text = getattr(message, "result", None)
            if result_text and not saw_any_delta:
                if settings.DEBUG:
                    logger.debug("claude.result size=%d", len(result_text))
                yield result_text


def is_first_iteration(current_plan: Optional[str]) -> bool:
    return current_plan is None


async def generate_plan(
    project_dir: str,
    user_raw_notes: str,
    prev_clarifying_questions: Optional[str],
    current_plan: Optional[str],
) -> AsyncGenerator[Tuple[ClaudeOutputType, str], None]:
    """Stream a plan for the given project based on raw notes.

    The stream includes only final result content (no thinking messages) and
    emits typed chunks tagged as plan content or clarifying questions.
    If a chunk contains both sections, it is split and yielded in order.
    """
    if is_first_iteration(current_plan):
        # First iteration - use standard system prompt and just user raw notes
        system_prompt = SYSTEM_PROMPT
        prompt = user_raw_notes
    else:
        # Non-first iteration - use specialized system prompt and include context
        system_prompt = SYSTEM_PROMPT_NON_FIRST_ITERATION

        # Build comprehensive prompt with previous context
        prompt_parts = []

        if current_plan:
            prompt_parts.append("## Previous Plan Draft\n")
            prompt_parts.append(current_plan)
            prompt_parts.append("\n\n")

        if prev_clarifying_questions:
            prompt_parts.append("## Previous Clarifying Questions\n")
            prompt_parts.append(prev_clarifying_questions)
            prompt_parts.append("\n\n")

        prompt_parts.append("## User Raw Notes\n")
        prompt_parts.append(user_raw_notes)

        prompt = "".join(prompt_parts)

    # Streaming classification state
    current_type: Optional[ClaudeOutputType] = None
    buffer: str = ""
    # To guard against splitting a header across chunk boundaries, retain a small tail
    max_header_len = ClaudeOutputManager.get_max_header_length()
    tail_keep = max(0, max_header_len - 1)
    om = ClaudeOutputManager  # Shorthand for cleaner code

    async for chunk in _query_claude_stream(
        working_directory=project_dir,
        system_prompt=system_prompt,
        prompt=prompt,
    ):
        if not chunk:
            continue

        buffer += chunk

        while True:
            # Initialize current section when first header appears
            if current_type is None:
                candidates = []

                # Check for all possible section headers
                for section in om.get_all_sections():
                    idx = buffer.find(section.header)
                    if idx != -1:
                        output_type = ClaudeOutputType(section.name)
                        candidates.append((idx, output_type))

                if not candidates:
                    # No header found yet; wait for more data
                    break

                candidates.sort(key=lambda x: x[0])
                first_idx, first_type = candidates[0]

                # Skip any preamble content - only emit content AFTER we see section headers
                # This ensures we don't incorrectly categorize content that appears before "# Plan name"
                current_type = first_type

                # Skip past the header itself, not just to where it starts
                header_text = None
                for section in om.get_all_sections():
                    if ClaudeOutputType(section.name) == first_type:
                        header_text = section.header
                        break

                if header_text:
                    header_end_idx = first_idx + len(header_text)
                    buffer = buffer[header_end_idx:]
                else:
                    buffer = buffer[first_idx:]
                # Continue with known current_type

            # With a known current_type, look for boundaries to other sections
            # Find all possible next section headers
            next_candidates = []
            for section in om.get_all_sections():
                if section.name != current_type.value:  # Don't look for current section header
                    idx = buffer.find(section.header)
                    if idx != -1:
                        output_type = ClaudeOutputType(section.name)
                        next_candidates.append((idx, output_type))

            if next_candidates:
                # Found a boundary to another section
                next_candidates.sort(key=lambda x: x[0])
                next_idx, next_type = next_candidates[0]

                # Emit the current section content (up to the next header)
                current_part = buffer[:next_idx]
                if current_part:
                    yield (current_type, current_part)

                # Move to next section, skipping past the header text
                header_text = None
                for section in om.get_all_sections():
                    if ClaudeOutputType(section.name) == next_type:
                        header_text = section.header
                        break

                if header_text:
                    header_end_idx = next_idx + len(header_text)
                    buffer = buffer[header_end_idx:]
                else:
                    buffer = buffer[next_idx:]

                current_type = next_type
                continue
            else:
                # No boundary found; flush safe portion leaving a small tail
                if len(buffer) > tail_keep:
                    emit_text = buffer[:-tail_keep] if tail_keep > 0 else buffer
                    if emit_text:
                        yield (current_type, emit_text)
                    buffer = buffer[-tail_keep:] if tail_keep > 0 else ""
                break

    # End of stream: flush anything remaining in buffer
    if buffer and current_type is not None:
        yield (current_type, buffer)


async def get_relevant_vocabulary(
    project_dir: str,
    optional_repo_hint: Optional[str] = None,
    max_files: int = 12,
    max_terms: int = 60,
) -> Dict[str, List[str]]:
    """Extract relevant files and terms using Claude Code and return mapped keys.

    Returns a dict with keys:
      - "relevent_files": List[str]  (note: spelling per consumer expectation)
      - "bespoke_terms": List[str]
    """
    prompt = build_vocab_prompt(optional_repo_hint, max_files, max_terms)

    # Collect the streamed JSON result
    collected: List[str] = []
    async for chunk in _query_claude_stream(
        working_directory=project_dir,
        system_prompt=None,
        prompt=prompt,
    ):
        if chunk:
            collected.append(chunk)

    raw_output = "".join(collected).strip()

    # Try to parse JSON strictly; if extra text sneaks in, attempt to extract the first JSON object
    try:
        parsed_json = json.loads(raw_output)
    except Exception:
        # Fallback: extract from first '{' to last '}'
        start = raw_output.find("{")
        end = raw_output.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed_json = json.loads(raw_output[start : end + 1])
            except Exception as err:  # pragma: no cover
                print(f"Error parsing JSON from Claude output: {err}", file=sys.stderr)
                parsed_json = {"relevant_files": [], "relevant_terms": []}
        else:
            parsed_json = {"relevant_files": [], "relevant_terms": []}

    relevant_files = parsed_json.get("relevant_files") or []
    relevant_terms = parsed_json.get("relevant_terms") or []

    # Enforce caps just in case
    relevant_files = list(relevant_files)[:max_files]
    relevant_terms = list(relevant_terms)[:max_terms]

    return {
        "relevent_files": relevant_files,
        "bespoke_terms": relevant_terms,
    }
