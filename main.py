#!/usr/bin/env python3
"""
Self-Healing CI/CD Pipeline  –  main entry point.

Usage:
    python main.py              # run once (check + fix if needed)
    python main.py --watch      # poll Jenkins in a loop
    python main.py --dry-run    # analyse only, don't patch or push
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time

from config import jenkins_cfg, pipeline_cfg
from crew import selfhealing_crew
from tools.jenkins_tools import CheckLastBuildStatusTool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("selfhealing")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _last_build_failed() -> tuple[bool, dict]:
    """Quick check using the tool directly (no LLM needed)."""
    tool = CheckLastBuildStatusTool()
    raw = tool._run()
    data = json.loads(raw)
    if data.get("error"):
        log.warning("Could not reach Jenkins: %s", data["error"])
        return False, data
    failed = data.get("result") == "FAILURE"
    return failed, data


def run_once(dry_run: bool = False) -> bool:
    """
    Run one cycle:
      1. Check Jenkins
      2. If failed → kick off the Crew
    Returns True if a fix was attempted.
    """
    failed, build_info = _last_build_failed()

    if not failed:
        status = build_info.get("result") or ("BUILDING" if build_info.get("building") else "UNKNOWN")
        log.info(
            "Build #%s is %s – nothing to do.",
            build_info.get("build_number", "?"),
            status,
        )
        return False

    log.info(
        "Build #%s FAILED – launching self-healing crew …",
        build_info.get("build_number"),
    )

    if dry_run:
        log.info("[DRY RUN] Would kick off the crew now. Exiting.")
        return False

    result = selfhealing_crew.kickoff()

    log.info("── Crew finished ──")
    log.info("Result:\n%s", result)
    return True


def watch_loop(dry_run: bool = False) -> None:
    """Poll Jenkins in a loop, healing on failure."""
    interval = pipeline_cfg.poll_interval
    max_retries = pipeline_cfg.max_retries
    consecutive_fixes = 0

    log.info(
        "Watching Jenkins job '%s' (branch: %s) every %ds …",
        jenkins_cfg.job_name,
        jenkins_cfg.branch,
        interval,
    )

    while True:
        try:
            fix_attempted = run_once(dry_run=dry_run)

            if fix_attempted:
                consecutive_fixes += 1
                if consecutive_fixes >= max_retries:
                    log.error(
                        "Reached %d consecutive fix attempts – stopping to "
                        "avoid infinite loop.  Manual intervention required.",
                        max_retries,
                    )
                    sys.exit(1)
                # Give Jenkins time to start the new build
                log.info("Waiting %ds before next poll …", interval * 2)
                time.sleep(interval * 2)
            else:
                consecutive_fixes = 0  # reset on success / non-failure
                time.sleep(interval)

        except KeyboardInterrupt:
            log.info("Interrupted – shutting down.")
            break
        except Exception:
            log.exception("Unexpected error in watch loop")
            time.sleep(interval)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Self-Healing CI/CD Pipeline")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Poll Jenkins continuously instead of running once.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect failures and analyse logs but don't push fixes.",
    )
    args = parser.parse_args()

    # Validate essential config
    if not jenkins_cfg.url or not jenkins_cfg.job_name:
        log.error(
            "JENKINS_URL and JENKINS_JOB_NAME must be set. "
            "Copy .env.example → .env and fill in your values."
        )
        sys.exit(1)

    if args.watch:
        watch_loop(dry_run=args.dry_run)
    else:
        run_once(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
