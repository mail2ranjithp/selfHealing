"""Centralised configuration loaded from .env / environment variables."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class JenkinsConfig:
    url: str = field(default_factory=lambda: os.getenv("JENKINS_URL", ""))
    user: str = field(default_factory=lambda: os.getenv("JENKINS_USER", ""))
    api_token: str = field(default_factory=lambda: os.getenv("JENKINS_API_TOKEN", ""))
    job_name: str = field(default_factory=lambda: os.getenv("JENKINS_JOB_NAME", ""))
    branch: str = field(default_factory=lambda: os.getenv("JENKINS_BRANCH", "main"))


@dataclass
class GitConfig:
    repo_url: str = field(default_factory=lambda: os.getenv("GIT_REPO_URL", ""))
    username: str = field(default_factory=lambda: os.getenv("GIT_USERNAME", ""))
    token: str = field(default_factory=lambda: os.getenv("GIT_TOKEN", ""))
    branch: str = field(default_factory=lambda: os.getenv("GIT_BRANCH", "main"))
    clone_dir: str = field(default_factory=lambda: os.getenv("GIT_CLONE_DIR", "/tmp/selfhealing-repo"))


@dataclass
class PipelineConfig:
    poll_interval: int = field(
        default_factory=lambda: int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    )
    llm_provider: str = field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "openai")
    )


jenkins_cfg = JenkinsConfig()
git_cfg = GitConfig()
pipeline_cfg = PipelineConfig()
