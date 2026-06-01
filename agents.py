"""CrewAI agent definitions for the self-healing CI/CD pipeline."""

from crewai import Agent, LLM

from config import pipeline_cfg
from tools import (
    CheckLastBuildStatusTool,
    FetchBuildLogTool,
    TriggerBuildTool,
    CloneRepoTool,
    ApplyFixTool,
    CommitAndPushTool,
)


# ─── LLM selection ────────────────────────────────────────────────────────────

def _build_llm() -> LLM:
    if pipeline_cfg.llm_provider == "anthropic":
        return LLM(model="anthropic/claude-sonnet-4-20250514")
    return LLM(model="openai/gpt-4o")


llm = _build_llm()


# ─── Agent 1 – Jenkins Monitor ────────────────────────────────────────────────

jenkins_monitor_agent = Agent(
    role="Jenkins Build Monitor",
    goal=(
        "Continuously watch the Jenkins job for the configured branch. "
        "Detect when the latest build has FAILED and collect the full "
        "console log so downstream agents can diagnose the problem."
    ),
    backstory=(
        "You are a vigilant DevOps sentinel. Your only job is to monitor "
        "Jenkins builds. When a build fails you immediately fetch the "
        "console log and hand it off for analysis."
    ),
    tools=[
        CheckLastBuildStatusTool(),
        FetchBuildLogTool(),
    ],
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


# ─── Agent 2 – Error Analyst / Fixer ─────────────────────────────────────────

error_analyst_agent = Agent(
    role="Build Error Analyst & Code Fixer",
    goal=(
        "Given a Jenkins console log from a failed build, identify the root "
        "cause — the exact file(s) and line(s) responsible — then produce a "
        "minimal, correct code fix (original snippet → fixed snippet)."
    ),
    backstory=(
        "You are a senior software engineer who has seen every kind of build "
        "failure: compilation errors, test failures, linting violations, "
        "dependency issues. You read raw logs with ease and always suggest "
        "the smallest safe change that resolves the failure."
    ),
    tools=[],  # analysis is pure LLM reasoning
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


# ─── Agent 3 – Code Patcher ──────────────────────────────────────────────────

code_patcher_agent = Agent(
    role="Code Patcher & Committer",
    goal=(
        "Clone or pull the repository, apply the code fix proposed by the "
        "analyst, commit with a clear message, and push to the remote branch."
    ),
    backstory=(
        "You are an automation bot responsible for applying approved patches. "
        "You are meticulous: you always verify the file path, ensure the "
        "original snippet exists, replace it, and then commit + push."
    ),
    tools=[
        CloneRepoTool(),
        ApplyFixTool(),
        CommitAndPushTool(),
    ],
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


# ─── Agent 4 – Build Re-trigger ──────────────────────────────────────────────

build_trigger_agent = Agent(
    role="Build Re-trigger Agent",
    goal=(
        "After the fix has been pushed, trigger a new Jenkins build and "
        "report the queue URL so the team can track the result."
    ),
    backstory=(
        "You are the final link in the self-healing chain. Once the patch "
        "is pushed, you kick off a fresh build and confirm it's queued."
    ),
    tools=[
        TriggerBuildTool(),
        CheckLastBuildStatusTool(),
    ],
    llm=llm,
    verbose=True,
    allow_delegation=False,
)
