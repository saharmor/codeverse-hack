#!/usr/bin/env python3
"""
Two-phase test harness for claude_service.generate_plan
Simulates iterative plan generation and saves each iteration to markdown files
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Tuple

from services.claude_service import ClaudeOutputType
from services.claude_service import generate_plan as generate_plan_structured

INITIAL_PROMPT = """
Create a web application for managing developer project tasks and notes.
The app should allow developers to:
- Create and organize project notes
- Track implementation tasks
- Generate development plans using AI assistance
- Collaborate with team members

I want this to be a modern web app with a clean UI.
"""

SECOND_ITERATION_FEEDBACK = """
Based on the initial plan, I have some additional requirements and answers to the clarifying questions:

- I prefer React with TypeScript for the frontend
- Use PostgreSQL for the database
- I want real-time collaboration features using WebSocket connections
- The AI assistance should integrate with Claude API
- Include user authentication with JWT tokens
- I want a responsive design that works well on mobile devices
- Add support for markdown formatting in notes
- Include basic project templates for common development workflows

Please update the plan to include these specific requirements and adjust the architecture accordingly.
"""

WORKING_DIRECTORY = "/Users/saharmor/Documents/codebase/codeverse-hack"  # Current project directory


async def run_iteration(
    iteration_num: int,
    user_raw_notes: str,
    prev_clarifying_questions: Optional[str] = None,
    current_plan: Optional[str] = None,
) -> Tuple[str, float]:
    """Run a single iteration and save the output to a markdown file.

    Returns:
        Tuple of (output_string, duration_in_seconds)
    """

    print(f"\n🚀 Running iteration {iteration_num}...")
    print(f"📁 Working directory: {WORKING_DIRECTORY}")
    print(f"📝 User notes length: {len(user_raw_notes)} characters")

    if current_plan:
        print(f"📋 Previous plan length: {len(current_plan)} characters")
    if prev_clarifying_questions:
        print(f"❓ Previous questions length: {len(prev_clarifying_questions)} characters")

    print(f"\n⏳ Generating plan (iteration {iteration_num})...")

    # Start timing
    start_time = time.time()

    # Collect all output from the generator
    output_parts = []
    plan_name_parts = []
    plan_parts = []
    clarify_parts = []
    async for out_type, chunk in generate_plan_structured(
        project_dir=WORKING_DIRECTORY,
        user_raw_notes=user_raw_notes,
        prev_clarifying_questions=prev_clarifying_questions,
        current_plan=current_plan,
    ):
        # Maintain original behavior: accumulate and print raw text
        output_parts.append(chunk)
        if out_type == ClaudeOutputType.PLAN_NAME:
            plan_name_parts.append(chunk)
        elif out_type == ClaudeOutputType.PLAN:
            plan_parts.append(chunk)
        elif out_type == ClaudeOutputType.CLARIFY_QUESTIONS:
            clarify_parts.append(chunk)

    # End timing
    end_time = time.time()
    duration = end_time - start_time

    full_output = "".join(output_parts)

    # Save combined output
    filename = f"plan_iter_{iteration_num}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_output)

    # Save separated outputs
    plan_name_output = "".join(plan_name_parts)
    plan_output = "".join(plan_parts)
    clarify_output = "".join(clarify_parts)

    filename_plan_name = f"plan_iter_{iteration_num}_plan_name.md"
    filename_plan = f"plan_iter_{iteration_num}_plan.md"
    filename_clarify = f"plan_iter_{iteration_num}_clarify_questions.md"

    with open(filename_plan_name, "w", encoding="utf-8") as f:
        f.write(plan_name_output)
    with open(filename_plan, "w", encoding="utf-8") as f:
        f.write(plan_output)
    with open(filename_clarify, "w", encoding="utf-8") as f:
        f.write(clarify_output)

    print(f"\n💾 Saved iteration {iteration_num} output to {filename}")
    print(f"💾 Saved plan name section to {filename_plan_name}")
    print(f"💾 Saved plan section to {filename_plan}")
    print(f"💾 Saved clarifying questions section to {filename_clarify}")
    print(f"📊 Output length: {len(full_output)} characters")
    print(f"⏱️ Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")

    return full_output, duration


def extract_plan_name_and_sections(
    output: str,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract the plan name, plan draft, and clarifying questions from the output."""

    lines = output.split("\n")
    plan_name_lines = []
    plan_lines = []
    questions_lines = []

    current_section = None

    for line in lines:
        line_lower = line.lower().strip()

        if "plan name" in line_lower and line.startswith("#"):
            current_section = "plan_name"
            continue
        elif "plan draft" in line_lower and line.startswith("#"):
            current_section = "plan"
            continue
        elif "clarifying questions" in line_lower and line.startswith("#"):
            current_section = "questions"
            continue

        if current_section == "plan_name":
            plan_name_lines.append(line)
        elif current_section == "plan":
            plan_lines.append(line)
        elif current_section == "questions":
            questions_lines.append(line)

    plan_name = "\n".join(plan_name_lines).strip() if plan_name_lines else None
    plan = "\n".join(plan_lines).strip() if plan_lines else None
    questions = "\n".join(questions_lines).strip() if questions_lines else None

    return plan_name, plan, questions


async def _main() -> None:
    print("🎯 Starting two-phase plan generation simulation")
    print("=" * 60)

    # Start overall timing
    overall_start_time = time.time()

    # Phase 1: Initial plan generation
    iteration_0_output, iteration_0_duration = await run_iteration(
        iteration_num=0,
        user_raw_notes=INITIAL_PROMPT,
        prev_clarifying_questions=None,
        current_plan=None,
    )

    # Extract plan name, plan, and questions from first iteration
    print("\n🔍 Extracting plan name, plan, and questions from iteration 0...")
    (
        extracted_plan_name,
        extracted_plan,
        extracted_questions,
    ) = extract_plan_name_and_sections(iteration_0_output)

    if extracted_plan_name:
        print(f"✅ Extracted plan name: {len(extracted_plan_name)} characters")
        print(f"📛 Plan name: {extracted_plan_name[:100]}{'...' if len(extracted_plan_name) > 100 else ''}")
    else:
        print("⚠️ Could not extract plan name from iteration 0")

    if extracted_plan:
        print(f"✅ Extracted plan: {len(extracted_plan)} characters")
    else:
        print("⚠️ Could not extract plan from iteration 0")

    if extracted_questions:
        print(f"✅ Extracted questions: {len(extracted_questions)} characters")
    else:
        print("⚠️ Could not extract questions from iteration 0")

    print("\n" + "=" * 60)

    # Phase 2: Refined plan generation with user feedback
    iteration_1_output, iteration_1_duration = await run_iteration(
        iteration_num=1,
        user_raw_notes=SECOND_ITERATION_FEEDBACK,
        prev_clarifying_questions=extracted_questions,
        current_plan=extracted_plan,
    )

    # End overall timing
    overall_end_time = time.time()
    total_duration = overall_end_time - overall_start_time

    print("\n" + "=" * 60)
    print("🎉 Two-phase simulation completed!")
    print("📁 Check plan_iter_0.md and plan_iter_1.md for the results")
    print("📁 Individual sections saved as separate files:")
    print("   • plan_iter_N_plan_name.md - Plan names")
    print("   • plan_iter_N_plan.md - Plan content")
    print("   • plan_iter_N_clarify_questions.md - Clarifying questions")
    print("\n📊 Timing Summary:")
    print(f"   • Iteration 0: {iteration_0_duration:.2f}s ({iteration_0_duration/60:.2f} min)")
    print(f"   • Iteration 1: {iteration_1_duration:.2f}s ({iteration_1_duration/60:.2f} min)")
    print(f"   • Total time: {total_duration:.2f}s ({total_duration/60:.2f} min)")
    print(f"   • Average per iteration: {(iteration_0_duration + iteration_1_duration)/2:.2f}s")

    # Calculate time difference between iterations
    time_diff = iteration_1_duration - iteration_0_duration
    percentage_change = (time_diff / iteration_0_duration) * 100 if iteration_0_duration > 0 else 0
    if time_diff > 0:
        print(f"   • Iteration 1 was {time_diff:.2f}s ({percentage_change:+.1f}%) slower than iteration 0")
    else:
        print(f"   • Iteration 1 was {abs(time_diff):.2f}s ({percentage_change:+.1f}%) faster than iteration 0")


if __name__ == "__main__":
    asyncio.run(_main())
