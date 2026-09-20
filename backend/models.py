"""
Pydantic v2 Domain Models and Strict Schemas for Document Intelligence Agent.
Enforces deterministic structured extraction and governance risk categorization.
"""

from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentType(str, Enum):
    SOLUTION_DESIGN_DOCUMENT = "SOLUTION_DESIGN_DOCUMENT"
    PRODUCT_REQUIREMENT_DOCUMENT = "PRODUCT_REQUIREMENT_DOCUMENT"
    VENDOR_CONTRACT = "VENDOR_CONTRACT"
    HSE_INSPECTION_REPORT = "HSE_INSPECTION_REPORT"
    UPSTREAM_OPERATIONAL_LOG = "UPSTREAM_OPERATIONAL_LOG"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class GovernanceVerdict(str, Enum):
    APPROVED = "APPROVED"
    CONDITIONAL_APPROVAL = "CONDITIONAL_APPROVAL"
    REJECTED_REVISION_REQUIRED = "REJECTED_REVISION_REQUIRED"

class ExtractedEntity(BaseModel):
    name: str = Field(..., description="Entity identifier (e.g., Asset Code, Vendor TIN, Cost Center, SLA)")
    value: str = Field(..., description="Normalized extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    section_reference: Optional[str] = Field(None, description="Document section or paragraph source")

class ComplianceRiskItem(BaseModel):
    category: str = Field(..., description="Risk domain: Financial, Information Security, HSE, SLA, Regulatory")
    risk_level: RiskLevel
    description: str = Field(..., description="Identified gap or compliance liability")
    mitigation_recommendation: str = Field(..., description="Actionable governance mitigation")

class DocumentAnalysisResult(BaseModel):
    document_title: str
    document_type: DocumentType
    summary: str
    governance_verdict: GovernanceVerdict
    completeness_score: float = Field(..., ge=0.0, le=100.0)
    extracted_entities: List[ExtractedEntity]
    identified_risks: List[ComplianceRiskItem]
    key_action_items: List[str]
    processing_metadata: Dict[str, str]

class AnalyzeDocumentRequest(BaseModel):
    document_text: str = Field(..., min_length=20, description="Raw unstructured document text")
    document_type: Optional[DocumentType] = DocumentType.SOLUTION_DESIGN_DOCUMENT
    model_name: Optional[str] = "qwen2.5:7b"
    temperature: Optional[float] = 0.1
    use_cache: Optional[bool] = True
