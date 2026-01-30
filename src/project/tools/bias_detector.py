"""
Bias Detector Tool for AEQUITAS (Fairness Auditor)
Detects biased language and suggests neutral alternatives
"""

import re
from typing import List, Dict, Tuple
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class BiasDetectorInput(BaseModel):
    """Input schema for Bias Detector"""
    text: str = Field(..., description="Text to analyze for bias")


class BiasDetector(BaseTool):
    name: str = "Bias Detector"
    description: str = """
    Analyzes text for various forms of bias including:
    - Gender bias and stereotyping
    - Racial and ethnic bias
    - Age-related bias (ageism)
    - Disability-related bias (ableism)
    - Socioeconomic bias
    - Cultural stereotyping
    - Loaded/charged language
    Returns flagged phrases with bias types and neutral alternatives.
    """
    args_schema: type[BaseModel] = BiasDetectorInput

    # Bias patterns and alternatives
    GENDER_BIAS: Dict[str, str] = {
        r"\bchairman\b": "chairperson",
        r"\bfireman\b": "firefighter",
        r"\bpoliceman\b": "police officer",
        r"\bstewardess\b": "flight attendant",
        r"\bwaitress\b": "server",
        r"\bmankind\b": "humankind",
        r"\bman-made\b": "artificial/synthetic",
        r"\bman hours\b": "person hours",
        r"\bmanpower\b": "workforce",
        r"\bfreshman\b": "first-year student",
        r"\bmailman\b": "mail carrier",
        r"\bsalesman\b": "salesperson",
        r"\bbusinessman\b": "businessperson",
        r"\bhe\s+or\s+she\b": "they",
        r"\bhis\s+or\s+her\b": "their",
    }

    STEREOTYPING_PHRASES: List[Dict[str, str]] = [
        {"pattern": r"women are (bad|worse|terrible) at", "type": "gender", "severity": "high"},
        {"pattern": r"men are (bad|worse|terrible) at", "type": "gender", "severity": "high"},
        {"pattern": r"women can't", "type": "gender", "severity": "high"},
        {"pattern": r"men can't", "type": "gender", "severity": "high"},
        {"pattern": r"all (women|men|asians|blacks|whites|mexicans|indians)", "type": "generalization", "severity": "high"},
        {"pattern": r"(women|men) always", "type": "gender", "severity": "medium"},
        {"pattern": r"(women|men) never", "type": "gender", "severity": "medium"},
        {"pattern": r"typical (woman|man|asian|black|white)", "type": "stereotyping", "severity": "high"},
        {"pattern": r"you people", "type": "othering", "severity": "medium"},
        {"pattern": r"those people", "type": "othering", "severity": "medium"},
        {"pattern": r"old people can't", "type": "ageism", "severity": "medium"},
        {"pattern": r"young people don't", "type": "ageism", "severity": "medium"},
        {"pattern": r"millennials are", "type": "ageism", "severity": "low"},
        {"pattern": r"boomers are", "type": "ageism", "severity": "low"},
    ]

    ABLEIST_TERMS: Dict[str, str] = {
        r"\bcrazy\b": "intense/unpredictable",
        r"\binsane\b": "extreme/unreasonable", 
        r"\blame\b": "inadequate/weak",
        r"\bdumb\b": "uninformed/silent",
        r"\bstupid\b": "unwise/ill-considered",
        r"\bidiot\b": "person who made a mistake",
        r"\bmoron\b": "person who erred",
        r"\bcrippled\b": "disabled/impaired",
        r"\bhandicapped\b": "person with a disability",
        r"\bblind to\b": "unaware of",
        r"\bdeaf to\b": "ignoring",
        r"\bturn a blind eye\b": "ignore",
    }

    LOADED_LANGUAGE: List[str] = [
        r"\bobviously\b",
        r"\bclearly\b",
        r"\beveryone knows\b",
        r"\bnobody believes\b",
        r"\bonly an idiot\b",
        r"\breal men\b",
        r"\breal women\b",
        r"\bnormal people\b",
        r"\bcommon sense\b",
    ]

    def _run(self, text: str) -> str:
        """Analyze text for bias and return results"""
        findings = []
        text_lower = text.lower()
        
        # Check gender-biased terms
        for pattern, alternative in self.GENDER_BIAS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                findings.append({
                    "type": "gender_bias",
                    "phrase": match.group(),
                    "severity": "low",
                    "alternative": alternative,
                    "explanation": f"Consider using gender-neutral term: '{alternative}'"
                })
        
        # Check stereotyping phrases
        for item in self.STEREOTYPING_PHRASES:
            matches = re.finditer(item["pattern"], text, re.IGNORECASE)
            for match in matches:
                findings.append({
                    "type": item["type"],
                    "phrase": match.group(),
                    "severity": item["severity"],
                    "alternative": "Avoid generalizations about groups",
                    "explanation": f"This phrase makes broad generalizations about a group"
                })
        
        # Check ableist terms
        for pattern, alternative in self.ABLEIST_TERMS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                findings.append({
                    "type": "ableism",
                    "phrase": match.group(),
                    "severity": "medium",
                    "alternative": alternative,
                    "explanation": f"This term can be considered ableist. Consider: '{alternative}'"
                })
        
        # Check loaded language
        for pattern in self.LOADED_LANGUAGE:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                findings.append({
                    "type": "loaded_language",
                    "phrase": match.group(),
                    "severity": "low",
                    "alternative": "Remove or rephrase",
                    "explanation": "This phrase can be dismissive or create false consensus"
                })
        
        if not findings:
            return "NO_BIAS_DETECTED: Text appears to be balanced and fair."
        
        # Calculate bias score (100 = perfect, decrease based on findings)
        severity_weights = {"low": 5, "medium": 15, "high": 25}
        total_penalty = sum(severity_weights.get(f["severity"], 10) for f in findings)
        bias_score = max(0, 100 - total_penalty)
        
        # Group findings by type
        by_type: Dict[str, List] = {}
        for f in findings:
            t = f["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(f)
        
        # Format output
        output = f"BIAS_ANALYSIS: Found {len(findings)} potential issues\n"
        output += f"FAIRNESS_SCORE: {bias_score}/100\n\n"
        
        for bias_type, items in by_type.items():
            output += f"=== {bias_type.upper().replace('_', ' ')} ({len(items)} found) ===\n"
            for item in items:
                output += f"  [{item['severity'].upper()}] \"{item['phrase']}\"\n"
                output += f"    → {item['explanation']}\n"
                output += f"    → Suggestion: {item['alternative']}\n\n"
        
        return output


def get_bias_detector() -> BiasDetector:
    """Factory function to get Bias Detector tool"""
    return BiasDetector()
