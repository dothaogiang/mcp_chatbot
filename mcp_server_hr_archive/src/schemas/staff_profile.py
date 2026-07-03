from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class StaffProfile(BaseModel):
    archiveCode: str
    fullName: Optional[str]
    position: Optional[str]
