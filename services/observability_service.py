"""
Observability & Monitoring Service (Stage 4 Harness).
Tracks agent workflows, tool execution traces, policy rejections, and latency for production diagnostics.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from pathlib import Path

# Setup logs directory
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
OBSERVABILITY_LOG_FILE = LOG_DIR / "agent_workflow.jsonl"


class ObservabilityHarness:
    """
    Stage 4 Harness: Observability & Monitoring.
    Captures telemetry, tool calls, latencies, and workflow traces to easily debug production issues.
    """

    def __init__(self, log_path: Path = OBSERVABILITY_LOG_FILE):
        self.log_path = log_path

    def log_event(self, event_type: str, payload: Dict[str, Any]):
        """Append a structured JSON event to the audit trail log."""
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "event_type": event_type,
            **payload,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    def trace_tool_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        execution_func: Callable[[], Any],
    ) -> Any:
        """
        Wraps a tool execution to record execution time, inputs, outcomes, and errors.
        """
        start_time = time.perf_counter()
        status = "SUCCESS"
        error_msg = None
        result = None

        try:
            result = execution_func()
            # If the result is a dict that indicates a policy rejection
            if isinstance(result, dict) and not result.get("success", True):
                status = "POLICY_REJECTED" if "policy_code" in result else "FAILED"
            return result
        except Exception as e:
            status = "EXCEPTION"
            error_msg = str(e)
            raise
        finally:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.log_event(
                event_type="TOOL_EXECUTION",
                payload={
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "status": status,
                    "elapsed_ms": elapsed_ms,
                    "error": error_msg,
                    "result_summary": self._summarize_result(result),
                },
            )

    def log_hitl_action(
        self,
        confirmation_id: str,
        action: str,
        amount: float,
        recipient: str,
        status: str,
    ):
        """Log Human-in-the-loop authorization events."""
        self.log_event(
            event_type="HITL_AUTHORIZATION",
            payload={
                "confirmation_id": confirmation_id,
                "action": action,
                "amount": amount,
                "recipient": recipient,
                "status": status,
            },
        )

    def _summarize_result(self, result: Any) -> Any:
        """Sanitize and summarize results for safe logging."""
        if isinstance(result, dict):
            summary = {k: v for k, v in result.items() if k not in ("candidate_beneficiaries",)}
            if "candidate_beneficiaries" in result:
                summary["candidate_count"] = len(result["candidate_beneficiaries"])
            return summary
        return str(result)[:200]

    # Google ADK Callbacks for automatic workflow interception
    def before_tool_callback(self, tool, args, kwargs):
        self.log_event(
            event_type="ADK_BEFORE_TOOL",
            payload={"tool": getattr(tool, "name", str(tool)), "args": args, "kwargs": kwargs},
        )

    def after_tool_callback(self, tool, result, args, kwargs):
        self.log_event(
            event_type="ADK_AFTER_TOOL",
            payload={
                "tool": getattr(tool, "name", str(tool)),
                "result_status": getattr(result, "get", lambda k, d=None: None)("status", "OK"),
            },
        )

    def on_tool_error_callback(self, tool, error, args, kwargs):
        self.log_event(
            event_type="ADK_TOOL_ERROR",
            payload={"tool": getattr(tool, "name", str(tool)), "error": str(error)},
        )


# Global singleton instance
observability = ObservabilityHarness()
