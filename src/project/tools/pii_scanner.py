"""
PII Scanner Tool for PRIVUS (Privacy Guardian)
Detects personally identifiable information in text
"""

import re
from typing import List, Dict, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class PIIScannerInput(BaseModel):
    """Input schema for PII Scanner"""
    text: str = Field(..., description="Text to scan for PII")


class PIIScanner(BaseTool):
    name: str = "PII Scanner"
    description: str = """
    Scans text for personally identifiable information (PII) including:
    - Social Security Numbers (SSN)
    - Credit Card Numbers
    - Phone Numbers
    - Email Addresses
    - IP Addresses
    - API Keys and Passwords
    - Dates of Birth
    - Physical Addresses
    Returns a list of detected PII with types, locations, and severity.
    """
    args_schema: type[BaseModel] = PIIScannerInput

    # PII Detection Patterns
    PII_PATTERNS: Dict[str, Dict[str, Any]] = {
        "ssn": {
            "pattern": r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b",
            "severity": "critical",
            "description": "Social Security Number"
        },
        "credit_card": {
            "pattern": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
            "severity": "critical",
            "description": "Credit Card Number"
        },
        "credit_card_formatted": {
            "pattern": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "severity": "critical",
            "description": "Credit Card Number (formatted)"
        },
        "email": {
            "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "severity": "high",
            "description": "Email Address"
        },
        "phone_us": {
            "pattern": r"\b(?:\+1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "severity": "medium",
            "description": "US Phone Number"
        },
        "phone_intl": {
            "pattern": r"\b\+?[1-9]\d{1,14}\b",
            "severity": "medium",
            "description": "International Phone Number"
        },
        "ip_address": {
            "pattern": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
            "severity": "medium",
            "description": "IP Address"
        },
        "api_key": {
            "pattern": r"\b(?:api[_-]?key|apikey|api[_-]?secret|secret[_-]?key)[\s:=]+['\"]?[A-Za-z0-9_\-]{20,}['\"]?\b",
            "severity": "critical",
            "description": "API Key"
        },
        "password": {
            "pattern": r"\b(?:password|passwd|pwd)[\s:=]+['\"]?[^\s'\"]{4,}['\"]?\b",
            "severity": "critical",
            "description": "Password"
        },
        "dob": {
            "pattern": r"\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12][0-9]|3[01])[/-](?:19|20)\d{2}\b|\b(?:19|20)\d{2}[/-](?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12][0-9]|3[01])\b",
            "severity": "medium",
            "description": "Date of Birth"
        },
        "aadhaar": {
            "pattern": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            "severity": "critical",
            "description": "Aadhaar Number (India)"
        },
        "pan": {
            "pattern": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
            "severity": "high",
            "description": "PAN Card Number (India)"
        }
    }

    def _run(self, text: str) -> str:
        """Scan text for PII and return results"""
        results = []
        text_lower = text.lower()
        
        for pii_type, config in self.PII_PATTERNS.items():
            pattern = config["pattern"]
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Mask the detected value for safety
                value = match.group()
                masked_value = self._mask_value(value, pii_type)
                
                results.append({
                    "type": pii_type,
                    "description": config["description"],
                    "severity": config["severity"],
                    "original_value": value,
                    "masked_value": masked_value,
                    "start_index": match.start(),
                    "end_index": match.end()
                })
        
        # Check for common sensitive keywords
        sensitive_keywords = ["password", "secret", "api key", "token", "credential", "ssn", "social security"]
        for keyword in sensitive_keywords:
            if keyword in text_lower:
                # Check if already detected by patterns
                already_detected = any(r["type"] in ["password", "api_key", "ssn"] for r in results)
                if not already_detected:
                    idx = text_lower.find(keyword)
                    results.append({
                        "type": "sensitive_keyword",
                        "description": f"Sensitive keyword detected: {keyword}",
                        "severity": "medium",
                        "original_value": keyword,
                        "masked_value": "[SENSITIVE]",
                        "start_index": idx,
                        "end_index": idx + len(keyword)
                    })
        
        if not results:
            return "NO_PII_DETECTED: Text appears to be clean of personally identifiable information."
        
        # Format results
        output = f"PII_DETECTED: Found {len(results)} potential PII items:\n\n"
        for i, item in enumerate(results, 1):
            output += f"{i}. [{item['severity'].upper()}] {item['description']}\n"
            output += f"   Value: {item['masked_value']}\n"
            output += f"   Position: {item['start_index']}-{item['end_index']}\n\n"
        
        return output

    def _mask_value(self, value: str, pii_type: str) -> str:
        """Mask PII value for safe logging"""
        if len(value) <= 4:
            return "*" * len(value)
        
        if pii_type in ["ssn", "aadhaar"]:
            return "***-**-" + value[-4:]
        elif pii_type in ["credit_card", "credit_card_formatted"]:
            return "**** **** **** " + value[-4:]
        elif pii_type == "email":
            parts = value.split("@")
            if len(parts) == 2:
                return parts[0][:2] + "***@" + parts[1]
            return "***@***"
        elif pii_type in ["phone_us", "phone_intl"]:
            return "***-***-" + value[-4:]
        elif pii_type in ["password", "api_key"]:
            return "[REDACTED]"
        else:
            return value[:2] + "*" * (len(value) - 4) + value[-2:]


def get_pii_scanner() -> PIIScanner:
    """Factory function to get PII Scanner tool"""
    return PIIScanner()
