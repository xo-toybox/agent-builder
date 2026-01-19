"""Security utilities for memory content validation.

Detects suspicious patterns that may indicate prompt injection attacks
or unsafe content that should be highlighted for user review.
"""

import re
from typing import TypedDict


class SuspiciousPattern(TypedDict):
    """A detected suspicious pattern in content."""

    pattern: str
    match: str
    description: str
    severity: str  # "warning" or "danger"


# Suspicious patterns to detect in memory content: (regex, description, severity)
# "danger" = high risk prompt injection indicators
# "warning" = potentially suspicious but may be legitimate
SUSPICIOUS_PATTERNS = [
    # Unconditional actions - DANGER (prompt injection indicators)
    (r"always\s+(do|send|forward|reply|respond)", "Unconditional action", "danger"),
    (r"automatically\s+(do|send|forward|reply|respond)", "Automatic action", "danger"),

    # Bypass verification - DANGER (prompt injection indicators)
    (r"never\s+(ask|check|verify|confirm|wait)", "Bypass verification", "danger"),
    (r"skip\s+(approval|verification|confirmation)", "Skip approval", "danger"),
    (r"without\s+(asking|checking|verifying)", "Without verification", "danger"),

    # Ignore instructions - DANGER (prompt injection indicators)
    (r"ignore\s+(previous|prior|user|system)", "Ignore instructions", "danger"),
    (r"disregard\s+(previous|prior|user|system)", "Disregard instructions", "danger"),
    (r"override\s+(instructions|settings|rules)", "Override settings", "danger"),

    # URLs (potential data exfiltration) - WARNING (may be legitimate)
    (r"https?://\S+", "Contains URL", "warning"),

    # Email addresses (potential data exfiltration) - WARNING (may be legitimate)
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "Contains email address", "warning"),

    # API keys / secrets patterns - DANGER
    (r"(api[_-]?key|secret|token|password)\s*[:=]", "Contains credential pattern", "danger"),

    # System commands - DANGER
    (r"(execute|run|eval)\s*\(", "Contains execution pattern", "danger"),

    # Base64 encoded content (potential obfuscation) - WARNING (may be legitimate)
    (r"[A-Za-z0-9+/]{40,}={0,2}", "Contains base64 encoded data", "warning"),
]


def detect_suspicious_patterns(content: str) -> list[SuspiciousPattern]:
    """Detect suspicious patterns in content.

    Args:
        content: Content to analyze

    Returns:
        List of detected suspicious patterns
    """
    results: list[SuspiciousPattern] = []

    for pattern, description, severity in SUSPICIOUS_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            # Handle tuple matches from groups
            match_str = match if isinstance(match, str) else match[0]
            results.append({
                "pattern": pattern,
                "match": match_str,
                "description": description,
                "severity": severity,
            })

    return results


def has_suspicious_content(content: str) -> bool:
    """Quick check if content has any suspicious patterns.

    Args:
        content: Content to check

    Returns:
        True if suspicious patterns detected
    """
    return len(detect_suspicious_patterns(content)) > 0
