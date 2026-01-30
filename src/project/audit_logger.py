"""
VERITAS Audit Logger
Immutable audit trail for all VERITAS decisions
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


class AuditLogger:
    """
    Logs all VERITAS decisions and creates an immutable audit trail.
    """
    
    def __init__(self, log_dir: str = "audit_logs"):
        """Initialize the audit logger with a log directory."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[str] = None
        
    def start_session(self, session_id: str) -> None:
        """Start a new audit session."""
        self.current_session = session_id
        session_file = self.log_dir / f"session_{session_id}.jsonl"
        
        # Log session start
        self._append_log(session_file, {
            "event": "session_start",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        })
    
    def log_agent_report(
        self,
        agent_name: str,
        report: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> None:
        """Log an individual agent's report."""
        sid = session_id or self.current_session
        if not sid:
            raise ValueError("No session ID available")
        
        session_file = self.log_dir / f"session_{sid}.jsonl"
        
        self._append_log(session_file, {
            "event": "agent_report",
            "timestamp": datetime.now().isoformat(),
            "session_id": sid,
            "agent": agent_name,
            "report": report
        })
    
    def log_trust_certificate(
        self,
        certificate: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> None:
        """Log the final trust certificate."""
        sid = session_id or self.current_session
        if not sid:
            raise ValueError("No session ID available")
        
        session_file = self.log_dir / f"session_{sid}.jsonl"
        
        self._append_log(session_file, {
            "event": "trust_certificate",
            "timestamp": datetime.now().isoformat(),
            "session_id": sid,
            "certificate": certificate
        })
    
    def log_decision(
        self,
        decision: str,
        reason: str,
        user_input: str,
        final_response: str,
        session_id: Optional[str] = None
    ) -> None:
        """Log the final decision (proceed/warn/block)."""
        sid = session_id or self.current_session
        if not sid:
            raise ValueError("No session ID available")
        
        session_file = self.log_dir / f"session_{sid}.jsonl"
        
        self._append_log(session_file, {
            "event": "decision",
            "timestamp": datetime.now().isoformat(),
            "session_id": sid,
            "decision": decision,
            "reason": reason,
            "user_input": user_input,
            "final_response": final_response
        })
    
    def end_session(
        self,
        processing_time_ms: int,
        session_id: Optional[str] = None
    ) -> None:
        """End the current audit session."""
        sid = session_id or self.current_session
        if not sid:
            raise ValueError("No session ID available")
        
        session_file = self.log_dir / f"session_{sid}.jsonl"
        
        self._append_log(session_file, {
            "event": "session_end",
            "timestamp": datetime.now().isoformat(),
            "session_id": sid,
            "processing_time_ms": processing_time_ms
        })
        
        self.current_session = None
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve the full history of a session."""
        session_file = self.log_dir / f"session_{session_id}.jsonl"
        
        if not session_file.exists():
            return []
        
        history = []
        with open(session_file, 'r') as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))
        
        return history
    
    def get_all_sessions(self) -> List[str]:
        """Get list of all session IDs."""
        sessions = []
        for f in self.log_dir.glob("session_*.jsonl"):
            session_id = f.stem.replace("session_", "")
            sessions.append(session_id)
        return sorted(sessions)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics across all sessions."""
        stats = {
            "total_sessions": 0,
            "decisions": {"proceed": 0, "warn": 0, "block": 0},
            "avg_processing_time_ms": 0,
            "common_issues": {}
        }
        
        processing_times = []
        
        for session_id in self.get_all_sessions():
            stats["total_sessions"] += 1
            history = self.get_session_history(session_id)
            
            for event in history:
                if event["event"] == "decision":
                    decision = event.get("decision", "unknown")
                    if decision in stats["decisions"]:
                        stats["decisions"][decision] += 1
                
                if event["event"] == "session_end":
                    pt = event.get("processing_time_ms", 0)
                    if pt > 0:
                        processing_times.append(pt)
        
        if processing_times:
            stats["avg_processing_time_ms"] = sum(processing_times) / len(processing_times)
        
        return stats
    
    def _append_log(self, filepath: Path, data: Dict[str, Any]) -> None:
        """Append a log entry to a file (JSONL format)."""
        with open(filepath, 'a') as f:
            f.write(json.dumps(data) + '\n')


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(log_dir: str = "audit_logs") -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(log_dir)
    return _audit_logger
