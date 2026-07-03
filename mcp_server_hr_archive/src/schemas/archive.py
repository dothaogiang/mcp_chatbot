from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ArchiveProject(BaseModel):
    name: str
    description: Optional[str] = None
    fileUrls: list[str] = []


class BorrowItem(BaseModel):
    borrowRequestId: str
    note: Optional[str] = None
    createdAt: Optional[datetime] = None


class StaffMetadataItem(BaseModel):
    fieldName: Optional[str] = None
    value: Optional[str] = None


class ArchiveSummary(BaseModel):
    id: str
    title: str
    arcFileCode: Optional[str] = None
    status: Optional[str] = None
    boxCode: Optional[str] = None
    warehouseName: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    roomNumber: Optional[str] = None
    description: Optional[str] = None
    totalDoc: Optional[int] = None
    language: Optional[str] = None
    maintenance: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    projects: list[ArchiveProject] = []
    staffMetadata: list[StaffMetadataItem] = []
    borrowItems: list[BorrowItem] = []