"""CrewAI task definitions for the self-healing CI/CD pipeline."""

from crewai import Task

from agents import (
    jenkins_monitor_agent,
    error_analyst_agent,
    code_patcher_agent,
    build_trigger_agent,
)


# ─── Task 1 – Detect failure & fetch log ─────────────────────────────────────

detect_failure_task = Task(
    description=(
        "1. Use the 'check_last_build_status' tool to get the latest build status.\n"
        "2. If the result is 'FAILURE', use 'fetch_build_log' with that build_number.\n"
        "3. Return the full console log along with the build number.\n"
        "4. If the build is SUCCESS or still running, return a short status message.\n"
    ),
    expected_output=(
        "A JSON object with keys:\n"
        "  - build_status: SUCCESS | FAILURE | BUILDING\n"
        "  - build_number: <int>\n"
        "  - console_log: <string>  (only when FAILURE)\n"
    ),
    agent=jenkins_monitor_agent,
)


# ─── Task 2 – Analyse the log & propose a fix ────────────────────────────────

analyse_and_fix_task = Task(
    description=(
        "You will receive the Jenkins console log from a failed build.\n\n"
        "Your job:\n"
        "1. Read the log carefully and identify the ROOT CAUSE — the exact error "
        "   message, the file path, and the line number if available.\n"
        "2. Determine the MINIMAL code change that fixes the error.\n"
        "3. Return your analysis as a JSON object with these exact keys:\n"
        "   - error_summary:    one-line human-readable summary of the failure\n"
        "   - file_path:        path relative to the repo root (e.g. src/app.py)\n"
        "   - original_snippet: the exact code that needs to change\n"
        "   - fixed_snippet:    the corrected replacement code\n"
        "   - explanation:      why this fix resolves the build failure\n\n"
        "IMPORTANT:\n"
        "- The original_snippet must be an EXACT substring of the current file.\n"
        "- Keep the change as small as possible.\n"
        "- If multiple files need changes, return an array of fix objects.\n"
    ),
    expected_output=(
        "A JSON object (or array of objects) with keys: "
        "error_summary, file_path, original_snippet, fixed_snippet, explanation."
    ),
    agent=error_analyst_agent,
    context=[detect_failure_task],
)


# ─── Task 3 – Apply the fix, commit & push ───────────────────────────────────

apply_fix_task = Task(
    description=(
        "You will receive one or more fix proposals (file_path, original_snippet, "
        "fixed_snippet) from the analyst.\n\n"
        "Steps:\n"
        "1. Use 'clone_or_pull_repo' to ensure the local copy is up to date.\n"
        "2. For each fix, use 'apply_code_fix' with the exact file_path, "
        "   original_snippet, and fixed_snippet.\n"
        "3. After all patches are applied, use 'commit_and_push' with a commit "
        "   message formatted as:\n"
        "     fix(selfhealing): <one-line error_summary>\n\n"
        "Return the commit result.\n"
    ),
    expected_output=(
        "A JSON object with keys: status (pushed | error), branch, commit_message."
    ),
    agent=code_patcher_agent,
    context=[analyse_and_fix_task],
)


# ─── Task 4 – Re-trigger the Jenkins build ───────────────────────────────────

retrigger_build_task = Task(
    description=(
        "The fix has been pushed. Now:\n"
        "1. Use 'trigger_jenkins_build' to start a new build.\n"
        "2. Return the queue ID / URL and a confirmation message.\n"
    ),
    expected_output=(
        "A JSON object with keys: status (triggered | error), job, queue_id, message."
    ),
    agent=build_trigger_agent,
    context=[apply_fix_task],
)
