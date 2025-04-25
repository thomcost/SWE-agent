#!/usr/bin/env python
"""
Dashboard hook for SWE-agent that logs activity to the dashboard database.
"""

from pathlib import Path
from typing import Any, Dict, List

from sweagent.agent.hooks.abstract import AbstractAgentHook
from sweagent.dashboard.logger import log_activity
from sweagent.types import AgentInfo, Trajectory, TrajectoryStep


class DashboardHook(AbstractAgentHook):
    """
    Hook that logs agent activities to the dashboard database.
    """

    def __init__(self, agent_id: str = None):
        """
        Initialize the hook.

        Args:
            agent_id: Optional identifier for the agent. If not provided, a random ID will be used.
        """
        import uuid
        self.agent_id = agent_id or f"agent-{uuid.uuid4().hex[:8]}"
        self._task_id = None
        self._model = None
        self._task_type = "Default"

    def on_init(self, agent) -> None:
        """Called when the hook is initialized with an agent."""
        self._model = agent.model.config.name if hasattr(agent, "model") and hasattr(agent.model, "config") else "unknown"

    def on_setup_attempt(self) -> None:
        """Called when a new attempt is set up."""
        import uuid
        self._task_id = f"task-{uuid.uuid4().hex[:8]}"

    def on_action_executed(self, step) -> None:
        """Called after an action is executed."""
        # Only log to dashboard if the agent has taken an action
        if hasattr(step, "action") and step.action and hasattr(step, "execution_time"):
            log_activity(
                agent_id=self.agent_id,
                task_id=self._task_id,
                task_type=self._task_type,
                status="success",
                model=self._model,
                tokens_used=0,  # Will be updated in on_step_done
                execution_time=step.execution_time,
            )

    def on_step_done(self, step, info: AgentInfo) -> None:
        """Called after a step is completed."""
        # Update with token information if available
        if hasattr(step, "output") and info.get("model_stats"):
            model_stats = info.get("model_stats", {})
            tokens_sent = model_stats.get("tokens_sent", 0)
            tokens_received = model_stats.get("tokens_received", 0)
            total_tokens = tokens_sent + tokens_received
            
            log_activity(
                agent_id=self.agent_id,
                task_id=self._task_id,
                task_type=self._task_type,
                status="success",
                model=self._model,
                tokens_used=total_tokens,
                execution_time=step.execution_time if hasattr(step, "execution_time") else 0.0,
            )

    def on_run_done(self, trajectory: Trajectory, info: AgentInfo) -> None:
        """Called when a run is completed."""
        # Log final status at the end of the run
        if info.get("exit_status"):
            status = "success" if info.get("exit_status") == "submitted" else "failure"
            error_message = ""
            
            if status == "failure":
                error_message = f"Exit status: {info.get('exit_status')}"
            
            # Calculate total execution time and tokens
            total_execution_time = sum(step["execution_time"] for step in trajectory if "execution_time" in step)
            total_tokens = 0
            if info.get("model_stats"):
                model_stats = info.get("model_stats", {})
                tokens_sent = model_stats.get("tokens_sent", 0)
                tokens_received = model_stats.get("tokens_received", 0)
                total_tokens = tokens_sent + tokens_received
            
            log_activity(
                agent_id=self.agent_id,
                task_id=self._task_id,
                task_type=self._task_type,
                status=status,
                model=self._model,
                tokens_used=total_tokens,
                execution_time=total_execution_time,
                error=error_message,
            )