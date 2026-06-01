# Self-Healing CI/CD Pipeline

An AI-powered agent system built with **CrewAI** that watches Jenkins builds, diagnoses failures from console logs, generates code fixes via LLM, commits the patch, and re-triggers the build — automatically.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      POLLING LOOP (main.py)                  │
│   Checks Jenkins every N seconds for FAILURE status          │
└──────────────┬───────────────────────────────────────────────┘
               │ failure detected
               ▼
┌──────────────────────────────────────────────────────────────┐
│  CREW (sequential pipeline)                                  │
│                                                              │
│  Agent 1: Jenkins Monitor                                    │
│     └─ fetch console log from failed build                   │
│                     │                                        │
│  Agent 2: Error Analyst                                      │
│     └─ LLM reads log → identifies root cause                 │
│     └─ proposes minimal fix (file, snippet, replacement)     │
│                     │                                        │
│  Agent 3: Code Patcher                                       │
│     └─ git pull → apply fix → commit & push                  │
│                     │                                        │
│  Agent 4: Build Trigger                                      │
│     └─ re-trigger Jenkins build                              │
└──────────────────────────────────────────────────────────────┘
```

## Setup

```bash
# 1. Clone this project
git clone <this-repo>
cd selfhealing-cicd

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env with your Jenkins URL, credentials, Git repo, and LLM API key
```

## Configuration (.env)

| Variable                 | Description                                     |
|--------------------------|-------------------------------------------------|
| `JENKINS_URL`            | Base URL of your Jenkins server                 |
| `JENKINS_USER`           | Jenkins username                                |
| `JENKINS_API_TOKEN`      | Jenkins API token (Manage Jenkins → API Token)  |
| `JENKINS_JOB_NAME`       | Job name (supports multibranch: `job/branch`)   |
| `JENKINS_BRANCH`         | Branch to watch                                 |
| `GIT_REPO_URL`           | HTTPS clone URL of the repo Jenkins builds      |
| `GIT_USERNAME`           | Git username for push                           |
| `GIT_TOKEN`              | Personal access token with push permissions     |
| `GIT_BRANCH`             | Branch to commit fixes to                       |
| `LLM_PROVIDER`           | `openai` or `anthropic`                         |
| `OPENAI_API_KEY`         | OpenAI key (if using openai)                    |
| `ANTHROPIC_API_KEY`      | Anthropic key (if using anthropic)              |
| `POLL_INTERVAL_SECONDS`  | Seconds between polls (default: 60)             |
| `MAX_RETRY_ATTEMPTS`     | Stop after N consecutive fix attempts (default: 3) |

## Usage

```bash
# Run once — check the latest build and fix if failed
python main.py

# Watch mode — poll Jenkins continuously
python main.py --watch

# Dry run — analyse failures but don't push any fixes
python main.py --dry-run

# Combined
python main.py --watch --dry-run
```

## Project Structure

```
selfhealing-cicd/
├── main.py              # Entry point, polling loop, CLI
├── crew.py              # CrewAI crew assembly
├── agents.py            # 4 agent definitions
├── tasks.py             # 4 task definitions
├── config.py            # Env-based configuration
├── tools/
│   ├── __init__.py
│   ├── jenkins_tools.py # CheckBuild, FetchLog, TriggerBuild
│   └── git_tools.py     # CloneRepo, ApplyFix, CommitAndPush
├── requirements.txt
├── .env.example
└── README.md
```

## Safety Guardrails

- **Max retries**: The watcher stops after `MAX_RETRY_ATTEMPTS` consecutive fix cycles to prevent infinite loops.
- **Minimal patches**: The analyst agent is instructed to propose the smallest possible change.
- **Dry-run mode**: Lets you validate the analysis without touching the repo.
- **Verbose logging**: All agent reasoning is printed so you can audit each decision.

## Extending

- **Slack/Teams notifications**: Add a 5th agent with a webhook tool to post results.
- **PR instead of direct push**: Swap `CommitAndPushTool` for a GitHub/GitLab PR creation tool.
- **Multi-repo support**: Parameterise `GIT_REPO_URL` and `JENKINS_JOB_NAME` per run.
- **Test-only failures**: Add logic in the analyst to distinguish compile errors from flaky tests.
