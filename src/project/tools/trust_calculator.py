"""
Trust Score Calculator Tool for CONCORDIA (Orchestrator)
Calculates unified trust score from all agent reports
"""

from typing import Dict, List, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class TrustCalculatorInput(BaseModel):
    """Input schema for Trust Calculator"""
    privacy_score: int = Field(..., ge=0, le=100, description="Privacy score from PRIVUS")
    bias_score: int = Field(..., ge=0, le=100, description="Bias/fairness score from AEQUITAS")
    transparency_score: int = Field(..., ge=0, le=100, description="Transparency score from LUMEN")
    ethics_score: int = Field(..., ge=0, le=100, description="Ethics score from ETHOS")
    critical_issues: Optional[str] = Field(default="", description="Any critical issues that require immediate blocking")


class TrustCalculator(BaseTool):
    name: str = "Trust Score Calculator"
    description: str = """
    Calculates the unified trust score from all guardian agent reports.
    Takes scores from PRIVUS, AEQUITAS, LUMEN, and ETHOS.
    Applies weighted averaging and threshold-based decision making.
    Returns overall score and final decision (proceed/warn/block).
    """
    args_schema: type[BaseModel] = TrustCalculatorInput

    # Score weights (should sum to 1.0)
    WEIGHTS: Dict[str, float] = {
        "privacy": 0.30,      # Privacy is critical
        "bias": 0.20,         # Fairness matters
        "transparency": 0.20,  # Explainability important
        "ethics": 0.30,       # Ethics is critical
    }

    # Thresholds for decisions
    BLOCK_THRESHOLD: int = 30      # Below this = block
    WARN_THRESHOLD: int = 60       # Below this = warn
    CRITICAL_THRESHOLD: int = 20   # Any single score below this = block

    def _run(
        self,
        privacy_score: int,
        bias_score: int,
        transparency_score: int,
        ethics_score: int,
        critical_issues: str = ""
    ) -> str:
        """Calculate unified trust score and make final decision"""
        
        scores = {
            "privacy": privacy_score,
            "bias": bias_score,
            "transparency": transparency_score,
            "ethics": ethics_score,
        }
        
        # Check for any critical issues that override scoring
        if critical_issues and len(critical_issues.strip()) > 0:
            return self._format_output(
                overall_score=0,
                scores=scores,
                decision="block",
                reason=f"Critical issue detected: {critical_issues}",
                conflicts=[]
            )
        
        # Check if any single score is critically low
        critical_failures = []
        for name, score in scores.items():
            if score < self.CRITICAL_THRESHOLD:
                critical_failures.append(f"{name.upper()}: {score}")
        
        if critical_failures:
            return self._format_output(
                overall_score=min(scores.values()),
                scores=scores,
                decision="block",
                reason=f"Critical failure in: {', '.join(critical_failures)}",
                conflicts=[]
            )
        
        # Calculate weighted average
        overall_score = sum(
            scores[name] * self.WEIGHTS[name]
            for name in scores
        )
        overall_score = int(round(overall_score))
        
        # Detect conflicts (when agents disagree significantly)
        conflicts = self._detect_conflicts(scores)
        
        # Determine decision based on overall score
        if overall_score < self.BLOCK_THRESHOLD:
            decision = "block"
            reason = "Overall trust score too low"
        elif overall_score < self.WARN_THRESHOLD:
            decision = "warn"
            reason = "Trust score indicates caution needed"
        else:
            decision = "proceed"
            reason = "All checks passed"
        
        return self._format_output(
            overall_score=overall_score,
            scores=scores,
            decision=decision,
            reason=reason,
            conflicts=conflicts
        )

    def _detect_conflicts(self, scores: Dict[str, int]) -> List[Dict]:
        """Detect significant disagreements between agents"""
        conflicts = []
        score_list = list(scores.items())
        
        for i, (name1, score1) in enumerate(score_list):
            for name2, score2 in score_list[i+1:]:
                diff = abs(score1 - score2)
                if diff > 40:  # Significant disagreement
                    # Determine how to resolve
                    if "ethics" in (name1, name2) or "privacy" in (name1, name2):
                        # Ethics and privacy take precedence
                        winner = name1 if scores[name1] < scores[name2] else name2
                        resolution = f"Deferring to stricter {winner} score for safety"
                    else:
                        resolution = "Averaging scores with slight penalty for disagreement"
                    
                    conflicts.append({
                        "agents": [name1.upper(), name2.upper()],
                        "scores": [score1, score2],
                        "resolution": resolution
                    })
        
        return conflicts

    def _format_output(
        self,
        overall_score: int,
        scores: Dict[str, int],
        decision: str,
        reason: str,
        conflicts: List[Dict]
    ) -> str:
        """Format the trust calculation output"""
        
        decision_emoji = {
            "proceed": "✅",
            "warn": "⚠️",
            "block": "❌"
        }
        
        output = "=" * 50 + "\n"
        output += "        TRUST SCORE CALCULATION\n"
        output += "=" * 50 + "\n\n"
        
        output += "INDIVIDUAL SCORES:\n"
        for name, score in scores.items():
            emoji = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
            weight = self.WEIGHTS[name]
            contribution = int(score * weight)
            output += f"  {emoji} {name.upper():15} {score:3d}/100 (weight: {weight:.0%}, contributes: {contribution})\n"
        
        output += f"\n{'=' * 50}\n"
        output += f"OVERALL TRUST SCORE: {overall_score}/100\n"
        output += f"DECISION: {decision_emoji.get(decision, '?')} {decision.upper()}\n"
        output += f"REASON: {reason}\n"
        output += f"{'=' * 50}\n"
        
        if conflicts:
            output += "\n⚡ CONFLICTS DETECTED:\n"
            for conflict in conflicts:
                output += f"  • {conflict['agents'][0]} ({conflict['scores'][0]}) vs "
                output += f"{conflict['agents'][1]} ({conflict['scores'][1]})\n"
                output += f"    Resolution: {conflict['resolution']}\n"
        
        return output


def get_trust_calculator() -> TrustCalculator:
    """Factory function to get Trust Calculator tool"""
    return TrustCalculator()
