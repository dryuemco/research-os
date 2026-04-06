from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.common.enums import ApprovalStatus, MemoryCategory


class DocumentSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str
    source_uri: str
    source_type: str = "internal"
    metadata_json: dict = Field(default_factory=dict)


class MemoryDocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    category: MemoryCategory
    source_id: str
    content_text: str
    version_label: str = "v1"
    provenance_json: dict = Field(default_factory=dict)
    sensitive: bool = False


class MemoryDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    category: MemoryCategory
    source_id: str
    checksum: str
    version_label: str
    sensitive: bool
    created_at: datetime


class ReusableBlockCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str | None = None
    block_key: str
    category: MemoryCategory
    title: str
    body_text: str
    tags: list[str] = Field(default_factory=list)
    provenance_json: dict = Field(default_factory=dict)


class ReusableBlockUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    body_text: str | None = None
    tags: list[str] | None = None
    approval_status: ApprovalStatus | None = None
    approved_by: str | None = None


class ReusableBlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    block_key: str
    category: MemoryCategory
    title: str
    body_text: str
    tags: list[str]
    approval_status: ApprovalStatus
    approved_by: str | None
    approved_at: str | None
    provenance_json: dict
    created_at: datetime


class RetrievalFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: list[MemoryCategory] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    approved_only: bool = True
    include_sensitive: bool = False


class RetrievalQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_text: str
    limit: int = 5
    task_type: str = "concept_note"
    filters: RetrievalFilter = Field(default_factory=RetrievalFilter)
    policy: RetrievalPolicy | None = None


class RetrievalBackendMode(StrEnum):
    LEXICAL = "lexical"
    VECTOR = "vector"
    HYBRID = "hybrid"


class RetrievalPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend_mode: RetrievalBackendMode = RetrievalBackendMode.HYBRID
    lexical_weight: float = 0.6
    vector_weight: float = 0.4
    category_weights: dict[MemoryCategory, float] = Field(default_factory=dict)
    max_context_chars: int = 6000
    max_per_category: int = 2
    min_confidence: float = 0.2
    freshness_bias: float = 0.0
    redundancy_penalty: float = 0.15
    approved_only_override: bool | None = None


class BlockProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block_id: str
    block_key: str
    category: MemoryCategory
    source_document_id: str | None = None
    provenance_json: dict = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block: ReusableBlockResponse
    relevance_score: float
    confidence: float
    backend_name: str = "lexical"
    normalized_score: float = 0.0
    provenance: BlockProvenance
    rationale: list[str] = Field(default_factory=list)
    selected_reason: str | None = None


class RetrievalContextAssembly(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose: str
    query: RetrievalQuery
    context_blocks: list[RetrievalResult] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)


class ExportPackagePreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    include_reviewer_logs: bool = True
    include_decomposition: bool = True
    include_reusable_evidence: bool = True


class ExportPackagePreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_name: str
    proposal_id: str
    package_items: list[dict] = Field(default_factory=list)
    unresolved_items: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
