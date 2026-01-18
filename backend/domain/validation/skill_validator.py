"""Validation utilities for Anthropic Agent Skills specification.

Implements name normalization and validation per the official spec:
- Max 64 characters
- Lowercase letters, numbers, hyphens only
- Cannot start or end with hyphen
- No consecutive hyphens

Reference: https://agentskills.io/specification
"""

import re


def normalize_skill_name(name: str) -> str:
    """Normalize skill name to Agent Skills spec format.

    Converts to lowercase, replaces spaces/underscores with hyphens,
    removes invalid characters, collapses consecutive hyphens.

    Args:
        name: Original skill name (e.g., "PDF Processing", "data_analysis")

    Returns:
        Normalized name (e.g., "pdf-processing", "data-analysis")

    Examples:
        >>> normalize_skill_name("PDF Processing")
        'pdf-processing'
        >>> normalize_skill_name("Data_Analysis")
        'data-analysis'
        >>> normalize_skill_name("--test--")
        'test'
        >>> normalize_skill_name("My  Complex   Name")
        'my-complex-name'
    """
    if not name:
        return ""

    # Convert to lowercase
    normalized = name.lower()

    # Replace spaces and underscores with hyphens
    normalized = re.sub(r"[_\s]+", "-", normalized)

    # Remove non-alphanumeric except hyphens
    normalized = re.sub(r"[^a-z0-9-]", "", normalized)

    # Collapse consecutive hyphens
    normalized = re.sub(r"-+", "-", normalized)

    # Strip leading/trailing hyphens
    normalized = normalized.strip("-")

    # Truncate to max length
    return normalized[:64]


def validate_skill_name(name: str) -> None:
    """Validate skill name against Agent Skills spec rules.

    Rules:
    - Max 64 characters
    - Lowercase letters, numbers, hyphens only
    - Cannot start or end with hyphen
    - No consecutive hyphens

    Args:
        name: Skill name to validate

    Raises:
        ValueError: If name violates spec constraints
    """
    if not name:
        raise ValueError("Skill name cannot be empty")

    if len(name) > 64:
        raise ValueError(
            f"Skill name too long ({len(name)} chars). Max 64 characters."
        )

    if not re.match(r"^[a-z0-9-]+$", name):
        raise ValueError(
            f"Skill name must contain only lowercase letters, numbers, and hyphens. "
            f"Got: '{name}'"
        )

    if name.startswith("-") or name.endswith("-"):
        raise ValueError(
            f"Skill name cannot start or end with hyphen. Got: '{name}'"
        )

    if "--" in name:
        raise ValueError(
            f"Skill name cannot contain consecutive hyphens. Got: '{name}'"
        )
