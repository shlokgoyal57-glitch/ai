"""
Safety Checker Tool for ETHOS (Ethical Oversight)
Checks for harmful content, dangerous requests, and ethical violations
"""

import re
from typing import List, Dict
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class SafetyCheckerInput(BaseModel):
    """Input schema for Safety Checker"""
    text: str = Field(..., description="Text to check for safety concerns")


class SafetyChecker(BaseTool):
    name: str = "Safety Checker"
    description: str = """
    Analyzes text for safety concerns including:
    - Dangerous/harmful instructions
    - Violence or threats
    - Self-harm content
    - Illegal activities
    - Misinformation patterns
    - Manipulation tactics
    - Hate speech
    Returns safety assessment with concerns and crisis resources if needed.
    """
    args_schema: type[BaseModel] = SafetyCheckerInput

    # Dangerous content patterns (broad categories - actual blocking would need more sophisticated detection)
    DANGEROUS_PATTERNS: List[Dict] = [
        {
            "pattern": r"\b(how to|make|create|build)\s*(a\s*)?(bomb|explosive|weapon|poison)\b",
            "category": "dangerous_instructions",
            "severity": "critical",
            "action": "block"
        },
        {
            "pattern": r"\b(hack|steal|break into|crack)\s*(password|account|system|computer)\b",
            "category": "illegal_activity",
            "severity": "high",
            "action": "warn"
        },
        {
            "pattern": r"\b(kill|murder|hurt|harm|attack)\s*(myself|yourself|someone|people)\b",
            "category": "violence_threat",
            "severity": "critical",
            "action": "block"
        },
        {
            "pattern": r"\b(suicide|self[- ]?harm|end my life|kill myself)\b",
            "category": "self_harm",
            "severity": "critical",
            "action": "block_with_resources"
        },
        {
            "pattern": r"\b(drug|cocaine|heroin|meth|fentanyl)\s*(deal|sell|make|cook|manufacture)\b",
            "category": "illegal_activity",
            "severity": "critical",
            "action": "block"
        },
    ]

    # Manipulation tactics
    MANIPULATION_PATTERNS: List[Dict] = [
        {
            "pattern": r"\b(pretend|act like|ignore|forget)\s*(you are|your|safety|rules|guidelines)\b",
            "category": "jailbreak_attempt",
            "severity": "medium",
            "action": "warn"
        },
        {
            "pattern": r"\b(dan|do anything now|evil mode|no restrictions)\b",
            "category": "jailbreak_attempt", 
            "severity": "medium",
            "action": "warn"
        },
        {
            "pattern": r"\bignore (all )?(previous|above|prior) (instructions|prompts|rules)\b",
            "category": "jailbreak_attempt",
            "severity": "high",
            "action": "block"
        },
    ]

    # Hate speech patterns  
    HATE_PATTERNS: List[Dict] = [
        {
            "pattern": r"\b(hate|kill all|eliminate)\s*(jews|muslims|christians|blacks|whites|asians|gays|women|men)\b",
            "category": "hate_speech",
            "severity": "critical",
            "action": "block"
        },
    ]

    # Crisis resources
    CRISIS_RESOURCES: Dict[str, str] = {
        "self_harm": """
🆘 CRISIS RESOURCES:
• National Suicide Prevention Lifeline: 988 (US)
• Crisis Text Line: Text HOME to 741741
• International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/
• iCall (India): 9152987821
• Vandrevala Foundation (India): 1860 2662 345
Please reach out - you are not alone.""",
        
        "violence_threat": """
⚠️ If you or someone else is in immediate danger, please contact:
• Emergency Services: 911 (US) / 112 (EU) / 100 (India)
• Local law enforcement""",
    }

    def _run(self, text: str) -> str:
        """Check text for safety concerns"""
        concerns = []
        text_lower = text.lower()
        
        # Check all pattern categories
        all_patterns = self.DANGEROUS_PATTERNS + self.MANIPULATION_PATTERNS + self.HATE_PATTERNS
        
        for pattern_def in all_patterns:
            matches = re.finditer(pattern_def["pattern"], text, re.IGNORECASE)
            for match in matches:
                concerns.append({
                    "matched_text": match.group(),
                    "category": pattern_def["category"],
                    "severity": pattern_def["severity"],
                    "action": pattern_def["action"]
                })
        
        if not concerns:
            return "SAFETY_CHECK_PASSED: No safety concerns detected. Content appears safe."
        
        # Determine overall safety level
        severities = [c["severity"] for c in concerns]
        if "critical" in severities:
            safety_level = "BLOCKED"
            ethics_score = 0
        elif "high" in severities:
            safety_level = "CAUTION"
            ethics_score = 30
        else:
            safety_level = "CAUTION"
            ethics_score = 60
        
        # Check if we need crisis resources
        crisis_resource = ""
        for concern in concerns:
            if concern["category"] in self.CRISIS_RESOURCES:
                crisis_resource = self.CRISIS_RESOURCES[concern["category"]]
                break
        
        # Format output
        output = f"SAFETY_LEVEL: {safety_level}\n"
        output += f"ETHICS_SCORE: {ethics_score}/100\n"
        output += f"CONCERNS_FOUND: {len(concerns)}\n\n"
        
        for i, concern in enumerate(concerns, 1):
            output += f"{i}. [{concern['severity'].upper()}] {concern['category'].replace('_', ' ').title()}\n"
            output += f"   Matched: \"{concern['matched_text']}\"\n"
            output += f"   Recommended Action: {concern['action'].upper()}\n\n"
        
        if crisis_resource:
            output += crisis_resource
        
        # Provide ethical alternatives
        output += "\n\n📚 ETHICAL ALTERNATIVES:\n"
        output += "• I cannot provide information that could cause harm.\n"
        output += "• I'm happy to help with safe and constructive alternatives.\n"
        output += "• Consider reaching out to appropriate professionals or resources.\n"
        
        return output


def get_safety_checker() -> SafetyChecker:
    """Factory function to get Safety Checker tool"""
    return SafetyChecker()
