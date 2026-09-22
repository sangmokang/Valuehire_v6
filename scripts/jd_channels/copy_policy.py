"""Shared portal and owner-email exclusion policy; raw audit sources stay separate."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


def exclusion_hits(text: str) -> list[str]:
    """Return rule IDs, never deleted text. Semantic review still covers paraphrases."""
    if not isinstance(text, str):
        raise TypeError('copy must be text')
    path = Path(__file__).resolve().parents[2] / 'contracts' / 'jd-registration.json'
    policy = json.loads(path.read_text(encoding='utf-8'))['copy_policy']
    patterns = policy['forbidden_patterns']
    if not patterns:
        raise ValueError('copy exclusion policy has no rules')
    normalized = unicodedata.normalize('NFKC', text)
    return [rule['id'] for rule in patterns
            if re.search(rule['pattern'], normalized, flags=re.IGNORECASE)]
