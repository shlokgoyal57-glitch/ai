from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SafetyLevel(str, Enum):
    """Safety classification levels"""
    SAFE = "safe"
    CAUTION = "caution"
    BLOCKED = "blocked"


class FinalDecision(str, Enum):
    """Final trust decision"""
    PROCEED = "proceed"
    WARN = "warn"
    BLOCK = "block"


class PIIEntity(BaseModel):
    type: str
    value: str
    start_index: int
    end_index: int
    confidence: float


class Redaction(BaseModel):
    original_text: str
    redacted_text: str
    reason: str


class PrivacyReport(BaseModel):
    pii_detected: List[PIIEntity] = Field(default_factory=list)
    privacy_score: int = Field(ge=0, le=100)
    redactions: List[Redaction] = Field(default_factory=list)
    gdpr_compliant: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class BiasFlag(BaseModel):
    phrase: str
    bias_type: str
    severity: str
    alternative: str


class BiasReport(BaseModel):
    bias_score: int = Field(ge=0, le=100)
    flagged_phrases: List[BiasFlag] = Field(default_factory=list)
    neutral_alternatives: List[str] = Field(default_factory=list)
    categories_detected: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class Source(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    confidence: float
    verification_status: str


class Claim(BaseModel):
    claim_text: str
    confidence: float
    source: Optional[Source] = None
    verifiable: bool


class TransparencyReport(BaseModel):
    confidence_percentage: float = Field(ge=0.0, le=100.0)
    reasoning_chain: List[str] = Field(default_factory=list)
    sources_cited: List[Source] = Field(default_factory=list)
    claims_verified: int = 0
    claims_unverified: int = 0
    claims: List[Claim] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class EthicalConcern(BaseModel):
    concern: str
    severity: str
    category: str
    recommendation: str


class EthicsReport(BaseModel):
    ethics_score: int = Field(ge=0, le=100)
    safety_level: str  # safe, caution, blocked
    concerns: List[EthicalConcern] = Field(default_factory=list)
    alternatives_suggested: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class ConflictResolution(BaseModel):
    conflict_description: str
    resolution_approach: str
    final_decision: str


class TrustCertificate(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    privacy: PrivacyReport
    bias: BiasReport
    transparency: TransparencyReport
    ethics: EthicsReport
    final_decision: str = Field(default="proceed", description="proceed, warn, or block")
    conflicts_resolved: List[ConflictResolution] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = None
    final_response: str = Field(default="", description="The final response to show user")
    orchestrator_notes: str = Field(default="", description="Notes from CONCORDIA")

    def format_report(self) -> str:
        """Format trust certificate for display"""
        def get_status(score: int) -> str:
            if score >= 80:
                return "✅"
            elif score >= 50:
                return "⚠️"
            return "❌"
        
        privacy_status = get_status(self.privacy.privacy_score)
        bias_status = get_status(self.bias.bias_score)
        transparency_status = get_status(int(self.transparency.confidence_percentage))
        ethics_status = get_status(self.ethics.ethics_score)
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🎯 VERITAS TRUST REPORT                    ║
╠══════════════════════════════════════════════════════════════╣
║ {privacy_status} Privacy Score:      {self.privacy.privacy_score:3d}/100
║ {bias_status} Bias Score:         {self.bias.bias_score:3d}/100
║ {transparency_status} Transparency:       {int(self.transparency.confidence_percentage):3d}/100
║ {ethics_status} Ethics Score:       {self.ethics.ethics_score:3d}/100
╠══════════════════════════════════════════════════════════════╣
║ 🎯 OVERALL TRUST SCORE: {self.overall_score:3d}/100
║ 📋 DECISION: {self.final_decision.upper():^10}
╚══════════════════════════════════════════════════════════════╝
"""
        return report


class AuditEntry(BaseModel):
    timestamp: datetime
    session_id: str
    user_input: str
    original_response: str
    trust_certificate: TrustCertificate
    final_response: str
    processing_time_ms: int
