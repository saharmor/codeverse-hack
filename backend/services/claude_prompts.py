"""
claude_prompts.py

Handles Claude output type management and system prompt generation.
Separated from claude_service.py to keep concerns clean.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


@dataclass(frozen=True)
class OutputSection:
    """Represents a Claude output section with its metadata."""

    name: str
    header: str
    description: str
    order: int


class ClaudeOutputManager:
    """Manages Claude output types and their associated metadata."""

    # Define all output sections
    PLAN_NAME = OutputSection(
        name="plan_name",
        header="# Plan name",
        description="A concise, descriptive name for the implementation plan",
        order=1,
    )

    PLAN = OutputSection(
        name="plan", header="# Plan draft", description="The detailed implementation plan content", order=2
    )

    CLARIFY_QUESTIONS = OutputSection(
        name="clarify_questions",
        header="# Clarifying questions",
        description="Questions to clarify missing information",
        order=3,
    )

    @classmethod
    def get_all_sections(cls) -> List[OutputSection]:
        """Get all output sections sorted by order."""
        return sorted([cls.PLAN_NAME, cls.PLAN, cls.CLARIFY_QUESTIONS], key=lambda x: x.order)

    @classmethod
    def get_section_by_name(cls, name: str) -> Optional[OutputSection]:
        """Get output section by name."""
        sections = {s.name: s for s in cls.get_all_sections()}
        return sections.get(name)

    @classmethod
    def get_section_by_header(cls, header: str) -> Optional[OutputSection]:
        """Get output section by header text."""
        for section in cls.get_all_sections():
            if section.header == header:
                return section
        return None

    @classmethod
    def get_max_header_length(cls) -> int:
        """Get the maximum length of all headers for buffer management."""
        return max(len(section.header) for section in cls.get_all_sections())


class ClaudeOutputType(str, Enum):
    """Output type enum that corresponds to section names."""

    PLAN_NAME = ClaudeOutputManager.PLAN_NAME.name
    PLAN = ClaudeOutputManager.PLAN.name
    CLARIFY_QUESTIONS = ClaudeOutputManager.CLARIFY_QUESTIONS.name


def _get_plan_guidelines(is_first_iteration: bool) -> str:
    """Get plan content guidelines section."""
    if is_first_iteration:
        return """- Produce a clear, organized outline breaking down the development into modules or tasks.
- Include structure, key steps, dependencies, technology stack, code architecture, and testing strategy.
- Use a **plan-and-solve** approach: first outline the overall plan, then optionally detail sub-steps."""
    else:
        return """- Review the previous plan and incorporate insights from the user's raw notes.
- Refine, expand, or modify the plan based on the new information provided.
- Address answered clarifying questions by updating the relevant plan sections.
- Maintain a structured approach: modules/tasks, dependencies, architecture, testing strategy.
- Use a **plan-and-solve** approach: first outline the overall updated plan, then detail sub-steps."""


def _get_clarifying_guidelines(is_first_iteration: bool) -> str:
    """Get clarifying questions guidelines section."""
    if is_first_iteration:
        return """- List any important missing information that would impact the plan's accuracy.
- Focus on user experience, feature edge cases, data inputs/outputs,
  integration requirements, constraints, or any ambiguity.
- No more than 8 clarifying questions; choose only the most important."""
    else:
        return """- Remove any questions that have been answered.
- Add new questions that arise from the updated context or user notes.
- Focus on remaining uncertainties about user experience, feature edge cases,
  data inputs/outputs, integration requirements, or constraints.
- No more than 8 clarifying questions total; prioritize the most important ones."""


def build_system_prompt(is_first_iteration: bool = True) -> str:
    """Build system prompt using the output manager structure."""
    om = ClaudeOutputManager

    if is_first_iteration:
        base_description = "Given the user's raw notes below, produce the output using the following strict format:"
        iteration_context = ""
    else:
        base_description = (
            "This is NOT the first iteration - you are reviewing and "
            "refining an existing plan based on additional context from the user."
        )
        iteration_context = """

You will be provided with:
1. **Previous Plan Draft** - The current plan that needs review
2. **Previous Clarifying Questions** - Questions that were asked before
3. **User Raw Notes** - Additional context, answers, or modifications from the user"""

    # Prepare strings that contain backslashes outside of f-string
    plan_name_guidelines = "Plan name guidelines:\\n- Suggest a clear"

    plan_content_type = "Plan" if is_first_iteration else "Updated plan"
    clarifying_type = "Clarifying" if is_first_iteration else "Updated clarifying"

    concise_or_refined = "concise" if is_first_iteration else "refined"
    plan_or_updated = "plan" if is_first_iteration else "updated plan"
    ending_period = "." if is_first_iteration else " with the remaining/open questions only."
    plan_characteristics_ending = "." if is_first_iteration else " of the refined plan."
    example_name = (
        "Smart Developer Task Management Platform"
        if is_first_iteration
        else "CodeVerse - AI-Powered Development Platform"
    )

    return f"""
You are **Claude Code**, an AI agent assistant specialized in helping developers
draft high-quality implementation plans. {base_description}{iteration_context}

Formatting requirements (critical):
- The very first line of your response must be exactly: `{om.PLAN_NAME.header}`.
- Do not include anything before that first line (no preface, greetings, or metadata).
- On the next line, write a {concise_or_refined}, descriptive name for this implementation plan.
- Follow with a blank line, then a section titled `{om.PLAN.header}`.
- Under that heading, write the {plan_or_updated} content in Markdown.
- Conclude with a section titled `{om.CLARIFY_QUESTIONS.header}`{ending_period}
- Do not use emojis in your response.

{plan_name_guidelines} that captures the essence of the project
- Keep it concise but informative (e.g., "Modern Task Management Web App", "Real-time Collaboration Platform")
- Focus on the main purpose and key characteristics{plan_characteristics_ending}
- EXAMPLE FORMAT:
  ```
  {om.PLAN_NAME.header}
  {example_name}

  {om.PLAN.header}
  [{plan_or_updated} content here]
  ```

{plan_content_type} content guidelines:
{_get_plan_guidelines(is_first_iteration)}

{clarifying_type} questions guidelines:
{_get_clarifying_guidelines(is_first_iteration)}
"""


def build_vocab_prompt(
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
1) relevant_files — the main/entry-point files in the **root** of the repo
(relative paths from root, no subpaths unless an entry point only exists under
a conventional subdir like `cmd/<app>/main.go` or `bin/*`).
2) relevant_terms — the high-signal terms (proper nouns, multiword phrases,
CLI commands, model names, API names) that repeatedly appear in code/README/config
and should be used as **custom vocabulary for a speech-to-text service**.

Why this matters: these terms will be passed to an STT engine as biasing vocabulary.
Include exact casing (e.g., "Claude Code", "Codeverse", "WebSocket", "gRPC",
"Next.js", "OpenAI"), multiword phrases ("CLI coding agents"), acronyms,
domain entities, product/feature names, CLI subcommands, environment variable keys,
major class/component names, and public API route names. Exclude generic words
("server", "request", "user") unless they are branded or uniquely significant
in this repo.

INPUTS (provided by the caller; if omitted, infer by reading the workspace):
{repo_hint_section}- max_files: integer cap for relevant_files (default {max_files}).
- max_terms: integer cap for relevant_terms (default {max_terms}).

SELECTION HEURISTICS
Relevant files (root-focused):
- Python: files containing `if __name__ == "__main__"`; `main.py`, `app.py`,
`serve.py`; entry points from `pyproject.toml [project.scripts]` or
`setup.cfg`/`setup.py`; `manage.py` (Django).
- Node/TS: `package.json` fields `"main"`, `"bin"`, `"exports"`, and scripts
like `"start"`, `"dev"`; root `index.(js|ts)`, `server.(js|ts)`, `next.config.js`
(Next.js uses `app/` or `pages/` for app entry, but root scripts may launch it).
- Go: `cmd/<app>/main.go` (treat as root entry if present), or root `main.go`.
- Rust: `src/main.rs`.
- Java/Kotlin: root build files; main launcher classes; Spring Boot `@SpringBootApplication`.
- C#: `Program.cs`.
- Ruby: `bin/*`, `config.ru`.
- Framework launchers and CLIs: anything referenced by Procfile,
Dockerfile `CMD/ENTRYPOINT`, Makefile primary targets, `justfile` default,
`bazel`/`pants` top targets.
Exclude: tests, examples, docs, migrations, vendored deps, build artifacts, lockfiles, images.

Relevant terms (keep signal high):
- Product/project names, app names, codenames.
- Feature flags, core domain nouns (e.g., "plan canvas", "agent runner").
- CLI names and subcommands (`codeverse plan`, `codeverse run --repo`).
- Prominent library/framework names actually used (e.g., "Windsurf", "Cursor",
"FastAPI", "Next.js", "Playwright"), major protocol names ("WebRTC", "SSE", "gRPC").
- Public API routes (`/api/plan`, `/v1/agents/run`), event types, queue/topic names.
- Environment variable keys (`CODEVERSE_API_KEY`, `OPENAI_MODEL`), config keys,
dataset/model names.
- Filenames (without paths) that are often referenced in docs/issues (`process_events.py`, `main.py`).
Deduplicate, preserve exact casing, keep multiword phrases intact. Prefer specificity over volume.

PROCEDURE
1) Read: repository tree, README, package/build files,
Dockerfile/Procfile/Makefile/justfile, primary app files in root,
and configs that declare entry points.
2) Identify root-level main files using the heuristics above. Keep to max_files by importance.
3) Collect candidate terms from names, configs, README, code identifiers/components,
CLI definitions, env/config keys, and any provided optional_repo_hint.
Filter to the most salient (frequency + centrality), keep to max_terms.
4) Sort relevant_files by likely launch order/importance; sort relevant_terms by importance (most important first).
5) Output strict JSON only. No comments, no trailing commas, no explanations.

OUTPUT SCHEMA (STRICT):
{{
  "relevant_files": ["<filename.ext>", "..."],
  "relevant_terms": ["<Exact Casing Term>", "..."]
}}

VALIDATION
- Always return both keys, even if arrays are empty.
- Paths in relevant_files should be **root-relative filenames** (e.g., "main.py").
Only include a subpath if conventional (e.g., "cmd/api/main.go", "bin/cli").
- Ensure JSON parses.

NOW DO THIS
- Use max_files = {max_files} and max_terms = {max_terms} unless the caller overrides.
- If you find strong hints of these terms, include them (case-preserved):
["Codeverse", "Claude Code", "CLI coding agents"].
- Return only the JSON object.
"""


# Generate the standard prompts
SYSTEM_PROMPT = build_system_prompt(is_first_iteration=True)
SYSTEM_PROMPT_NON_FIRST_ITERATION = build_system_prompt(is_first_iteration=False)
