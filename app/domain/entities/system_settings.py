"""Pure domain entity for SystemSettings — zero framework imports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemSettings:
    key: str
    value: str
    description: Optional[str] = None
    id: Optional[int] = None
