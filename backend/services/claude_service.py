"""
claude_service.py

Provides an async generator API to stream only the final result content from
Claude Code, suitable for consumption by other modules.
"""

from __future__ import annotations

import json
import sys
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional, Tuple

try:
    from claude_code_sdk import ClaudeCodeOptions, query
except Exception:  # pragma: no cover
    print(
        "Error: Failed to import 'claude_code_sdk'.\nInstall it with: pip install claude-code-sdk",
        file=sys.stderr,
    )
    raise


# Section indicator headers used across prompts and streaming logic
PLAN_HEADER = "# Plan draft"
CLARIFY_HEADER = "# Clarifying questions"


SYSTEM_PROMPT = f"""
You are **Claude Code**, an AI agent assistant specialized in helping developers draft high-quality implementation plans. Given the user's raw notes below, produce the output using the following strict format:

Formatting requirements (critical):
- The very first line of your response must be exactly: `{PLAN_HEADER}`.
- Do not include anything before that first line (no preface, greetings, or metadata).
- Under that heading, write the plan content in Markdown.
- Conclude with a section titled `{CLARIFY_HEADER}`.
- Do not use emojis in your response.

Plan content guidelines:
- Produce a clear, organized outline breaking down the development into modules or tasks.
- Include structure, key steps, dependencies, technology stack, code architecture, and testing strategy.
- Use a **plan-and-solve** approach: first outline the overall plan, then optionally detail sub-steps.

Clarifying questions guidelines:
- List any important missing information that would impact the plan's accuracy.
- Focus on user experience, feature edge cases, data inputs/outputs, integration requirements, constraints, or any ambiguity.
- No more than 8 clarifying questions; choose only the most important.
"""

SYSTEM_PROMPT_NON_FIRST_ITERATION = f"""
You are **Claude Code**, an AI agent assistant specialized in helping developers draft high-quality implementation plans. This is NOT the first iteration - you are reviewing and refining an existing plan based on additional context from the user.

You will be provided with:
1. **Previous Plan Draft** - The current plan that needs review
2. **Previous Clarifying Questions** - Questions that were asked before
3. **User Raw Notes** - Additional context, answers, or modifications from the user

Formatting requirements (critical):
- The very first line of your response must be exactly: `{PLAN_HEADER}`.
- Do not include anything before that first line (no preface, greetings, or metadata).
- Under that heading, write the updated plan content in Markdown.
- Conclude with a section titled `{CLARIFY_HEADER}` with the remaining/open questions only.
- Do not use emojis in your response.

Updated plan guidelines:
- Review the previous plan and incorporate insights from the user's raw notes.
- Refine, expand, or modify the plan based on the new information provided.
- Address answered clarifying questions by updating the relevant plan sections.
- Maintain a structured approach: modules/tasks, dependencies, architecture, testing strategy.
- Use a **plan-and-solve** approach: first outline the overall updated plan, then detail sub-steps.

Updated clarifying questions guidelines:
- Remove any questions that have been answered.
- Add new questions that arise from the updated context or user notes.
- Focus on remaining uncertainties about user experience, feature edge cases, data inputs/outputs, integration requirements, or constraints.
- No more than 8 clarifying questions total; prioritize the most important ones.
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


def is_first_iteration(current_plan: Optional[str]) -> bool:
    return current_plan is None


class ClaudeOutputType(str, Enum):
    PLAN = "plan"
    CLARIFY_QUESTIONS = "clarify_questions"


async def generate_plan(
    project_dir: str,
    user_raw_notes: str,
    prev_clarfying_questions: Optional[str],
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

        if prev_clarfying_questions:
            prompt_parts.append("## Previous Clarifying Questions\n")
            prompt_parts.append(prev_clarfying_questions)
            prompt_parts.append("\n\n")

        prompt_parts.append("## User Raw Notes\n")
        prompt_parts.append(user_raw_notes)

        prompt = "".join(prompt_parts)

    # Streaming classification state
    current_type: Optional[ClaudeOutputType] = None
    buffer: str = ""
    # To guard against splitting a header across chunk boundaries, retain a small tail
    max_header_len = max(len(PLAN_HEADER), len(CLARIFY_HEADER))
    tail_keep = max(0, max_header_len - 1)

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
                plan_idx = buffer.find(PLAN_HEADER)
                clarify_idx = buffer.find(CLARIFY_HEADER)
                candidates = []
                if plan_idx != -1:
                    candidates.append((plan_idx, ClaudeOutputType.PLAN))
                if clarify_idx != -1:
                    candidates.append((clarify_idx, ClaudeOutputType.CLARIFY_QUESTIONS))

                if not candidates:
                    # No header found yet; wait for more data
                    break

                candidates.sort(key=lambda x: x[0])
                first_idx, first_type = candidates[0]

                # Emit any preamble (rare) as belonging to the first section we see
                if first_idx > 0:
                    preamble = buffer[:first_idx]
                    if preamble:
                        yield (first_type, preamble)

                current_type = first_type
                buffer = buffer[first_idx:]
                # Continue with known current_type

            # With a known current_type, look for a boundary to the other section
            if current_type == ClaudeOutputType.PLAN:
                next_idx = buffer.find(CLARIFY_HEADER)
                if next_idx != -1:
                    plan_part = buffer[:next_idx]
                    if plan_part:
                        yield (ClaudeOutputType.PLAN, plan_part)
                    buffer = buffer[next_idx:]
                    current_type = ClaudeOutputType.CLARIFY_QUESTIONS
                    # Loop to process remaining buffer under new type
                    continue
                else:
                    # No boundary yet; flush safe portion leaving a small tail to catch partial header
                    if len(buffer) > tail_keep:
                        emit_text = buffer[:-tail_keep] if tail_keep > 0 else buffer
                        if emit_text:
                            yield (ClaudeOutputType.PLAN, emit_text)
                        buffer = buffer[-tail_keep:] if tail_keep > 0 else ""
                    break

            if current_type == ClaudeOutputType.CLARIFY_QUESTIONS:
                # Normally the last section; still guard if plan header appears again
                next_idx = buffer.find(PLAN_HEADER)
                if next_idx != -1:
                    clarify_part = buffer[:next_idx]
                    if clarify_part:
                        yield (ClaudeOutputType.CLARIFY_QUESTIONS, clarify_part)
                    buffer = buffer[next_idx:]
                    current_type = ClaudeOutputType.PLAN
                    continue
                else:
                    if len(buffer) > tail_keep:
                        emit_text = buffer[:-tail_keep] if tail_keep > 0 else buffer
                        if emit_text:
                            yield (ClaudeOutputType.CLARIFY_QUESTIONS, emit_text)
                        buffer = buffer[-tail_keep:] if tail_keep > 0 else ""
                    break

    # End of stream: flush anything remaining in buffer
    if buffer and current_type is not None:
        yield (current_type, buffer)


def _build_vocab_prompt(
    optional_repo_hint: Optional[str],
    max_files: int,
    max_terms: int,
) -> str:
    """Build the vocabulary extraction prompt for Claude Code.

    The prompt instructs Claude Code to read the repository and output strict JSON
    with keys "relevant_files" and "relevant_terms".
    """
    repo_hint_section = f"- optional_repo_hint: {optional_repo_hint}\n" if optional_repo_hint else ""

    return f"""
You are Claude Code with access to the project repository. Your task is to extract:
1) relevant_files — the main/entry-point files in the **root** of the repo (relative paths from root, no subpaths unless an entry point only exists under a conventional subdir like `cmd/<app>/main.go` or `bin/*`).
2) relevant_terms — the high-signal terms (proper nouns, multiword phrases, CLI commands, model names, API names) that repeatedly appear in code/README/config and should be used as **custom vocabulary for a speech-to-text service**.

Why this matters: these terms will be passed to an STT engine as biasing vocabulary. Include exact casing (e.g., “Claude Code”, “Codeverse”, “WebSocket”, “gRPC”, “Next.js”, “OpenAI”), multiword phrases (“CLI coding agents”), acronyms, domain entities, product/feature names, CLI subcommands, environment variable keys, major class/component names, and public API route names. Exclude generic words (“server”, “request”, “user”) unless they are branded or uniquely significant in this repo.

INPUTS (provided by the caller; if omitted, infer by reading the workspace):
{repo_hint_section}- max_files: integer cap for relevant_files (default {max_files}).
- max_terms: integer cap for relevant_terms (default {max_terms}).

SELECTION HEURISTICS
Relevant files (root-focused):
- Python: files containing `if __name__ == "__main__"`; `main.py`, `app.py`, `serve.py`; entry points from `pyproject.toml [project.scripts]` or `setup.cfg`/`setup.py`; `manage.py` (Django).
- Node/TS: `package.json` fields `"main"`, `"bin"`, `"exports"`, and scripts like `"start"`, `"dev"`; root `index.(js|ts)`, `server.(js|ts)`, `next.config.js` (Next.js uses `app/` or `pages/` for app entry, but root scripts may launch it).
- Go: `cmd/<app>/main.go` (treat as root entry if present), or root `main.go`.
- Rust: `src/main.rs`.
- Java/Kotlin: root build files; main launcher classes; Spring Boot `@SpringBootApplication`.
- C#: `Program.cs`.
- Ruby: `bin/*`, `config.ru`.
- Framework launchers and CLIs: anything referenced by Procfile, Dockerfile `CMD/ENTRYPOINT`, Makefile primary targets, `justfile` default, `bazel`/`pants` top targets.
Exclude: tests, examples, docs, migrations, vendored deps, build artifacts, lockfiles, images.

Relevant terms (keep signal high):
- Product/project names, app names, codenames.
- Feature flags, core domain nouns (e.g., “plan canvas”, “agent runner”).
- CLI names and subcommands (`codeverse plan`, `codeverse run --repo`).
- Prominent library/framework names actually used (e.g., “Windsurf”, “Cursor”, “FastAPI”, “Next.js”, “Playwright”), major protocol names (“WebRTC”, “SSE”, “gRPC”).
- Public API routes (`/api/plan`, `/v1/agents/run`), event types, queue/topic names.
- Environment variable keys (`CODEVERSE_API_KEY`, `OPENAI_MODEL`), config keys, dataset/model names.
- Filenames (without paths) that are often referenced in docs/issues (`process_events.py`, `main.py`).
Deduplicate, preserve exact casing, keep multiword phrases intact. Prefer specificity over volume.

PROCEDURE
1) Read: repository tree, README, package/build files, Dockerfile/Procfile/Makefile/justfile, primary app files in root, and configs that declare entry points.
2) Identify root-level main files using the heuristics above. Keep to max_files by importance.
3) Collect candidate terms from names, configs, README, code identifiers/components, CLI definitions, env/config keys, and any provided optional_repo_hint. Filter to the most salient (frequency + centrality), keep to max_terms.
4) Sort relevant_files by likely launch order/importance; sort relevant_terms by importance (most important first).
5) Output strict JSON only. No comments, no trailing commas, no explanations.

OUTPUT SCHEMA (STRICT):
{{
  "relevant_files": ["<filename.ext>", "..."],
  "relevant_terms": ["<Exact Casing Term>", "..."]
}}

VALIDATION
- Always return both keys, even if arrays are empty.
- Paths in relevant_files should be **root-relative filenames** (e.g., "main.py"). Only include a subpath if conventional (e.g., "cmd/api/main.go", "bin/cli").
- Ensure JSON parses.

NOW DO THIS
- Use max_files = {max_files} and max_terms = {max_terms} unless the caller overrides.
- If you find strong hints of these terms, include them (case-preserved): ["Codeverse", "Claude Code", "CLI coding agents"].
- Return only the JSON object.
"""


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
    prompt = _build_vocab_prompt(optional_repo_hint, max_files, max_terms)

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
    parsed: Dict[str, List[str]]
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


# -----------------------------------------------------------------------------
# Backwards-compatible API for business router (streams raw strings)
# -----------------------------------------------------------------------------


def _build_user_notes_from_context(plan_context: Dict[str, object]) -> Tuple[str, Optional[str], Optional[str]]:
    """Construct rich user notes and optional previous sections from plan_context.

    Returns (user_notes, prev_clarifying_questions, current_plan_text)
    """
    plan = plan_context.get("plan")
    repository = plan_context.get("repository")
    existing_artifact = plan_context.get("existing_artifact")
    chat_history = plan_context.get("chat_history", [])
    user_message = plan_context.get("user_message")

    parts: List[str] = ["# Code Planning Session", ""]

    # Basic context
    if plan is not None:
        try:
            parts.extend(
                [
                    "## Plan Context",
                    f"Name: {getattr(plan, 'name', '')}",
                    f"Target Branch: {getattr(plan, 'target_branch', '')}",
                    f"Description: {getattr(plan, 'description', '') or 'No description provided'}",
                    "",
                ]
            )
        except Exception:
            pass

    if repository is not None:
        try:
            parts.extend(
                [
                    "## Repository",
                    f"Name: {getattr(repository, 'name', '')}",
                    f"Path: {getattr(repository, 'path', '')}",
                    "",
                ]
            )
        except Exception:
            pass

    # Existing artifact as context
    current_plan_text: Optional[str] = None
    prev_questions_text: Optional[str] = None
    if isinstance(existing_artifact, dict):
        try:
            parts.extend(["## Current Plan Artifact", "```json", json.dumps(existing_artifact, indent=2), "```", ""])
        except Exception:
            pass
        # Try extracting structured fields if present
        for key in ("clarifying_questions", "questions"):
            if key in existing_artifact and isinstance(existing_artifact[key], (list, str)):
                prev_questions_text = (
                    "\n".join(existing_artifact[key])
                    if isinstance(existing_artifact[key], list)
                    else str(existing_artifact[key])
                )
                break
        for key in ("plan", "draft", "overview"):
            if key in existing_artifact and isinstance(existing_artifact[key], (dict, list, str)):
                try:
                    current_plan_text = (
                        json.dumps(existing_artifact[key], indent=2)
                        if isinstance(existing_artifact[key], (dict, list))
                        else str(existing_artifact[key])
                    )
                except Exception:
                    current_plan_text = str(existing_artifact[key])
                break

    # Recent chat messages (last few)
    if isinstance(chat_history, list) and chat_history:
        parts.extend(["## Previous Conversation", ""])
        recent = chat_history[-5:] if len(chat_history) > 5 else chat_history
        for msg in recent:
            role = (msg or {}).get("role", "user") if isinstance(msg, dict) else "user"
            content = (msg or {}).get("content", "") if isinstance(msg, dict) else str(msg)
            parts.append(f"**{str(role).title()}:** {content}")
            parts.append("")

    # Current request
    parts.extend(
        [
            "## Current Request",
            f"**User:** {user_message}",
            "",
            "## Instructions",
            "Provide a structured implementation plan. Follow the formatting instructions at the top of the system prompt.",
        ]
    )

    return ("\n".join(parts), prev_questions_text, current_plan_text)


async def generate_plan_business(plan_context: Dict[str, object]) -> AsyncGenerator[str, None]:
    """Business-facing streaming function returning raw string chunks.

    Builds a rich context from `plan_context`, calls the structured `generate_plan`
    in this module, and yields only text chunks suitable for SSE/streaming.
    """
    # Build user notes and optional prior sections
    user_notes, prev_questions, current_plan_text = _build_user_notes_from_context(plan_context)

    repository = plan_context.get("repository")
    project_dir = str(getattr(repository, "path", "")) if repository is not None else "."

    async for out_type, chunk in generate_plan(
        project_dir=project_dir,
        user_raw_notes=user_notes,
        prev_clarfying_questions=prev_questions,
        current_plan=current_plan_text,
    ):
        # Discard the type for the business API; stream only text
        if chunk:
            yield chunk
