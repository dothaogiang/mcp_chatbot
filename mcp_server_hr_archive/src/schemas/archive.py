from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List


class ArchiveBase(BaseModel):
    id: str
    title: Optional[str]
    summary: Optional[str]


class ArchiveDetail(ArchiveBase):
    files: Optional[List[dict]]
