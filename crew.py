"""Assemble the self-healing CI/CD Crew."""

from crewai import Crew, Process

from agents import (
    jenkins_monitor_agent,
    error_analyst_agent,
    code_patcher_agent,
    build_trigger_agent,
)
from tasks import (
    detect_failure_task,
    analyse_and_fix_task,
    apply_fix_task,
    retrigger_build_task,
)


selfhealing_crew = Crew(
    agents=[
        jenkins_monitor_agent,
        error_analyst_agent,
        code_patcher_agent,
        build_trigger_agent,
    ],
    tasks=[
        detect_failure_task,
        analyse_and_fix_task,
        apply_fix_task,
        retrigger_build_task,
    ],
    process=Process.sequential,  # each task feeds into the next
    verbose=True,
)
