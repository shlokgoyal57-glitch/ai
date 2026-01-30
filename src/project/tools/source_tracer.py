"""
Source Tracer Tool for LUMEN (Transparency Engine)
Traces reasoning and assesses claim confidence
"""

import re
from typing import List, Dict
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class SourceTracerInput(BaseModel):
    """Input schema for Source Tracer"""
    text: str = Field(..., description="Text to analyze for claims and sources")


class SourceTracer(BaseTool):
    name: str = "Source Tracer"
    description: str = """
    Analyzes text for transparency and explainability:
    - Extracts claims and statements of fact
    - Assesses confidence levels for each claim
    - Identifies reasoning chains
    - Flags unverified or speculative statements
    - Checks for black-box assertions
    Returns transparency assessment with confidence scores.
    """
    args_schema: type[BaseModel] = SourceTracerInput

    # Patterns that indicate uncertainty
    UNCERTAINTY_MARKERS: List[str] = [
        r"\b(might|may|could|possibly|perhaps|probably)\b",
        r"\b(I think|I believe|I assume|I guess)\b",
        r"\b(it seems|it appears|it looks like)\b",
        r"\b(reportedly|allegedly|supposedly)\b",
        r"\b(uncertain|unclear|not sure|don't know)\b",
    ]

    # Patterns that indicate high confidence
    CONFIDENCE_MARKERS: List[str] = [
        r"\b(certainly|definitely|absolutely|always|never)\b",
        r"\b(proven|established|confirmed|verified)\b",
        r"\b(according to|research shows|studies show)\b",
        r"\b(is|are|was|were)\b(?!\s+(possible|likely|maybe))",
    ]

    # Patterns indicating black-box assertions
    BLACK_BOX_PATTERNS: List[str] = [
        r"\bjust (trust|believe|accept)\b",
        r"\beveryone knows\b",
        r"\bit's obvious\b",
        r"\bcommon knowledge\b",
        r"\bgoes without saying\b",
        r"\bno need to explain\b",
    ]

    # Claim extraction patterns
    CLAIM_PATTERNS: List[str] = [
        r"([A-Z][^.!?]*(?:is|are|was|were|will|can|should|must)[^.!?]*[.!?])",
        r"([A-Z][^.!?]*(?:always|never|all|every|no one)[^.!?]*[.!?])",
    ]

    def _run(self, text: str) -> str:
        """Analyze text for transparency and trace sources"""
        
        # Split into sentences for analysis
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        claims = []
        total_confidence = 0
        
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue
                
            confidence = self._assess_sentence_confidence(sentence)
            claim_type = self._classify_claim_type(sentence)
            
            claims.append({
                "text": sentence.strip(),
                "confidence": confidence,
                "type": claim_type,
                "verifiable": claim_type in ["factual", "statistical"],
            })
            total_confidence += confidence
        
        # Check for black-box assertions
        black_box_issues = []
        for pattern in self.BLACK_BOX_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                black_box_issues.append(match.group())
        
        # Calculate overall transparency score
        if claims:
            avg_confidence = total_confidence / len(claims)
        else:
            avg_confidence = 50
        
        # Penalize for black-box assertions
        transparency_score = int(avg_confidence - (len(black_box_issues) * 10))
        transparency_score = max(0, min(100, transparency_score))
        
        # Count verifiable vs non-verifiable
        verifiable = sum(1 for c in claims if c["verifiable"])
        non_verifiable = len(claims) - verifiable
        
        # Format output
        output = f"TRANSPARENCY_SCORE: {transparency_score}/100\n"
        output += f"OVERALL_CONFIDENCE: {avg_confidence:.1f}%\n"
        output += f"CLAIMS_ANALYZED: {len(claims)}\n"
        output += f"VERIFIABLE: {verifiable} | NON-VERIFIABLE: {non_verifiable}\n\n"
        
        if black_box_issues:
            output += "⚠️ BLACK-BOX ASSERTIONS DETECTED:\n"
            for issue in black_box_issues:
                output += f"  • \"{issue}\" - Consider providing reasoning\n"
            output += "\n"
        
        output += "=== CLAIM ANALYSIS ===\n"
        for i, claim in enumerate(claims[:10], 1):  # Limit to first 10
            conf_emoji = "🟢" if claim["confidence"] >= 70 else "🟡" if claim["confidence"] >= 40 else "🔴"
            output += f"{i}. {conf_emoji} [{claim['confidence']}%] ({claim['type']})\n"
            output += f"   \"{claim['text'][:100]}{'...' if len(claim['text']) > 100 else ''}\"\n\n"
        
        if len(claims) > 10:
            output += f"... and {len(claims) - 10} more claims\n"
        
        output += "\n=== REASONING CHAIN ===\n"
        output += "• Text analyzed for factual claims\n"
        output += "• Confidence assessed based on hedging language\n"
        output += "• Black-box assertions flagged\n"
        output += f"• Final transparency score: {transparency_score}/100\n"
        
        return output

    def _assess_sentence_confidence(self, sentence: str) -> int:
        """Assess confidence level of a sentence (0-100)"""
        confidence = 60  # Base confidence
        
        # Check uncertainty markers
        for pattern in self.UNCERTAINTY_MARKERS:
            if re.search(pattern, sentence, re.IGNORECASE):
                confidence -= 15
        
        # Check confidence markers
        for pattern in self.CONFIDENCE_MARKERS:
            if re.search(pattern, sentence, re.IGNORECASE):
                confidence += 10
        
        return max(0, min(100, confidence))

    def _classify_claim_type(self, sentence: str) -> str:
        """Classify the type of claim"""
        sentence_lower = sentence.lower()
        
        # Statistical claims
        if re.search(r'\d+%|\d+\s*(percent|million|billion|thousand)', sentence):
            return "statistical"
        
        # Opinion markers
        if re.search(r'\b(I think|I believe|in my opinion|I feel)\b', sentence, re.IGNORECASE):
            return "opinion"
        
        # Recommendation
        if re.search(r'\b(should|recommend|suggest|advise)\b', sentence, re.IGNORECASE):
            return "recommendation"
        
        # Question
        if sentence.strip().endswith("?"):
            return "question"
        
        # Default to factual assertion
        return "factual"


def get_source_tracer() -> SourceTracer:
    """Factory function to get Source Tracer tool"""
    return SourceTracer()
