from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel


class StaffMetadataField(BaseModel):
    name: str
    value: Optional[str] = None
    code: str


class ExtractedDataField(BaseModel):
    code: str
    name: str
    value: Optional[Any] = None
    default: Optional[bool] = None


class StaffDocument(BaseModel):
    documentName: str
    extractedData: list[ExtractedDataField] = []


class StaffDocumentType(BaseModel):
    documentTypeName: str
    configTemplate: Optional[str] = None
    documents: list[StaffDocument] = []


class StaffProfile(BaseModel):
    archiveName: str
    archiveCode: str
    metadata: list[StaffMetadataField] = []
    documentTypes: list[StaffDocumentType] = []