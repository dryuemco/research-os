from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.domain.common.enums import ApprovalStatus, MemoryCategory, OpportunityState, UserRole
from app.domain.identity_models import User
from app.domain.institutional_memory.models import (
    DocumentSource,
    MemoryChunk,
    MemoryDocument,
    ReusableEvidenceBlock,
)
from app.domain.operations.models import Notification
from app.domain.opportunity_discovery.models import InterestProfile, MatchResult, Opportunity
from app.domain.partner_intelligence.models import PartnerProfile
from app.domain.proposal_factory.models import Proposal
from app.schemas.audit import AuditEventSchema
from app.schemas.proposal import ProposalWorkspaceCreateRequest
from app.security.passwords import hash_password
from app.services.audit_service import AuditService
from app.services.operational_loop_service import OperationalLoopService
from app.services.opportunity_state_service import OpportunityStateService
from app.services.proposal_service import ProposalService

DEMO_USER_EMAIL = "pilot-admin@example.org"
DEMO_USERNAME = "pilot-admin"
DEMO_PROFILE_NAME = "Pilot Demo Profile"
DEMO_DOC_SOURCE_URI = "seed://pilot-demo"
DEMO_PARTNER_NAMES = ["Demo Partner Lab", "Iberia Health Data Hub"]


@dataclass(slots=True)
class DemoBootstrapResult:
    opportunities_loaded: int
    matches_created: int
    notifications_created: int
    proposal_created: bool


class DemoSeedService:
    """Creates a deterministic, repeatable pilot demo dataset via explicit invocation."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def bootstrap(
        self,
        *,
        fixture_path: str,
        reset_demo_state: bool = False,
        create_demo_proposal: bool = True,
    ) -> DemoBootstrapResult:
        if reset_demo_state:
            self._reset_demo_state()

        user = self._ensure_demo_user()
        self._ensure_interest_profile(user_id=user.id)
        self._ensure_partner_profiles()
        self._ensure_memory_blocks()
        OperationalLoopService(self.db).ensure_default_jobs()

        records = self._load_fixture_records(fixture_path)
        ingest_run = OperationalLoopService(self.db).run_ingestion_job(
            source_name="funding_call_scaffold",
            trigger_source="demo-bootstrap",
            run_matching_after=True,
            records=records,
        )
        summary = ingest_run.result_summary or {}

        proposal_created = False
        if create_demo_proposal:
            proposal_created = self._ensure_demo_proposal(owner_id=user.id)

        notifications_created = self.db.scalar(select(func.count()).select_from(Notification))
        matches_created = self.db.scalar(select(func.count()).select_from(MatchResult))

        self.audit.emit(
            AuditEventSchema(
                event_type="demo_bootstrap_completed",
                entity_type="system",
                entity_id="pilot_demo",
                actor_type="user",
                actor_id=user.id,
                payload={
                    "records_loaded": summary.get("total_records", 0),
                    "created": summary.get("created_count", 0),
                    "updated": summary.get("updated_count", 0),
                    "reset_demo_state": reset_demo_state,
                    "proposal_created": proposal_created,
                },
            )
        )
        self.db.flush()

        return DemoBootstrapResult(
            opportunities_loaded=summary.get("total_records", 0),
            matches_created=matches_created or 0,
            notifications_created=notifications_created or 0,
            proposal_created=proposal_created,
        )

    def _load_fixture_records(self, fixture_path: str) -> list[dict]:
        payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        records = payload.get("records", [])
        if not isinstance(records, list) or not records:
            raise ValueError("Fixture must define a non-empty 'records' list")
        return records

    def _ensure_demo_user(self) -> User:
        user = self.db.scalar(
            select(User).where((User.username == DEMO_USERNAME) | (User.email == DEMO_USER_EMAIL))
        )
        if user is not None:
            return user

        user = User(
            username=DEMO_USERNAME,
            password_hash=hash_password("demo-bootstrap-internal-only"),
            full_name="Pilot Admin",
            email=DEMO_USER_EMAIL,
            display_name="Pilot Admin",
            role=UserRole.ADMIN,
            team_name="grant-office",
            org_name="rpos-internal",
            is_active=True,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def _ensure_interest_profile(self, *, user_id: str) -> InterestProfile:
        profile = self.db.scalar(
            select(InterestProfile).where(InterestProfile.name == DEMO_PROFILE_NAME)
        )
        if profile is not None:
            return profile

        profile = InterestProfile(
            user_id=user_id,
            name=DEMO_PROFILE_NAME,
            parameters_json={
                "allowed_programs": ["horizon", "erasmus+"],
                "preferred_keywords": ["ai", "climate", "health", "digital twin"],
                "required_keywords": ["ai"],
                "target_roles": ["coordinator", "work_package_lead"],
                "min_budget_total": 1000000,
                "weights": {"keyword_overlap": 0.7, "budget_fit": 0.3},
            },
        )
        self.db.add(profile)
        self.db.flush()
        return profile

    def _ensure_partner_profiles(self) -> None:
        partners = [
            {
                "partner_name": "Demo Partner Lab",
                "legal_name": "Demo Partner Research Lab GmbH",
                "country_code": "DE",
                "organization_type": "research_org",
                "capability_tags": ["ai", "climate", "evaluation"],
                "program_participation": ["horizon"],
                "role_suitability": {"coordinator": 0.82, "beneficiary": 0.92},
            },
            {
                "partner_name": "Iberia Health Data Hub",
                "legal_name": "Iberia Health Data Hub S.L.",
                "country_code": "ES",
                "organization_type": "sme",
                "capability_tags": ["health", "data spaces", "federated learning"],
                "program_participation": ["horizon", "erasmus+"],
                "role_suitability": {"beneficiary": 0.88, "technology_provider": 0.91},
            },
        ]
        for partner_data in partners:
            existing = self.db.scalar(
                select(PartnerProfile).where(
                    PartnerProfile.partner_name == partner_data["partner_name"]
                )
            )
            if existing:
                continue
            self.db.add(
                PartnerProfile(
                    **partner_data,
                    source_metadata={"source": "demo_seed"},
                    intelligence_notes="Seeded profile for pilot dashboard walkthrough.",
                    active=True,
                )
            )
        self.db.flush()

    def _ensure_memory_blocks(self) -> None:
        source = self.db.scalar(
            select(DocumentSource).where(DocumentSource.source_uri == DEMO_DOC_SOURCE_URI)
        )
        if source is None:
            source = DocumentSource(
                source_name="pilot_demo_seed",
                source_uri=DEMO_DOC_SOURCE_URI,
                source_type="seed",
                metadata_json={"seed": "demo"},
            )
            self.db.add(source)
            self.db.flush()

        document = self.db.scalar(
            select(MemoryDocument).where(MemoryDocument.title == "Pilot Capability Snapshot")
        )
        if document is None:
            body = (
                "RPOS pilot team has delivered prior Horizon projects on climate resilience, "
                "clinical AI validation, and interoperable data spaces."
            )
            document = MemoryDocument(
                title="Pilot Capability Snapshot",
                category=MemoryCategory.ORGANIZATION_PROFILE,
                source_id=source.id,
                content_text=body,
                checksum="seed-pilot-capability-snapshot-v1",
                version_label="v1",
                provenance_json={"seed": "demo"},
                sensitive=False,
            )
            self.db.add(document)
            self.db.flush()

            self.db.add(
                MemoryChunk(
                    document_id=document.id,
                    chunk_index=0,
                    chunk_text=body,
                    token_estimate=46,
                    metadata_json={"seed": "demo", "section": "overview"},
                )
            )

        block = self.db.scalar(
            select(ReusableEvidenceBlock).where(
                ReusableEvidenceBlock.block_key == "demo-capability-ai-climate"
            )
        )
        if block is None:
            self.db.add(
                ReusableEvidenceBlock(
                    document_id=document.id,
                    block_key="demo-capability-ai-climate",
                    category=MemoryCategory.REUSABLE_PROPOSAL_BLOCK,
                    title="AI-enabled climate risk analytics capability",
                    body_text=(
                        "The consortium combines validated machine-learning pipelines, "
                        "federated data governance, and prior deployment experience in "
                        "municipal climate adaptation."
                    ),
                    tags=["ai", "climate", "risk_analytics"],
                    approval_status=ApprovalStatus.APPROVED,
                    approved_by=DEMO_USER_EMAIL,
                    approved_at="2026-03-01T00:00:00Z",
                    provenance_json={"seed": "demo", "source": "pilot_capability_snapshot"},
                )
            )
        self.db.flush()

    def _ensure_demo_proposal(self, *, owner_id: str) -> bool:
        shortlisted = self.db.scalars(
            select(Opportunity)
            .where(Opportunity.state == OpportunityState.SHORTLISTED)
            .order_by(Opportunity.created_at.desc())
        ).all()
        if not shortlisted:
            return False

        target = shortlisted[0]
        existing = self.db.scalar(select(Proposal).where(Proposal.opportunity_id == target.id))
        if existing is not None:
            return False

        OpportunityStateService(self.db).apply_decision(
            target,
            "approve",
            actor_type="user",
            actor_id=owner_id,
            reason="demo bootstrap approved for proposal workspace",
        )

        ProposalService(self.db).create_workspace(
            ProposalWorkspaceCreateRequest(
                opportunity_id=target.id,
                owner_id=owner_id,
                name=f"Demo Workspace - {target.title[:48]}",
                template_type="horizon-ria",
                page_limit=45,
                mandatory_sections=["excellence", "impact", "implementation"],
                compliance_rules=[{"rule": "ethics_self_assessment_required"}],
            )
        )
        self.db.flush()
        return True

    def _reset_demo_state(self) -> None:
        demo_doc_ids = self.db.scalars(
            select(MemoryDocument.id).where(MemoryDocument.title == "Pilot Capability Snapshot")
        ).all()
        demo_profile = self.db.scalar(
            select(InterestProfile).where(InterestProfile.name == DEMO_PROFILE_NAME)
        )
        if demo_profile is not None:
            self.db.execute(delete(MatchResult).where(MatchResult.profile_id == demo_profile.id))
            self.db.execute(delete(Proposal).where(Proposal.owner_id == demo_profile.user_id))
            self.db.execute(delete(InterestProfile).where(InterestProfile.id == demo_profile.id))

        self.db.execute(delete(Notification).where(Notification.recipient_user_id == "ops-admin"))
        self.db.execute(
            delete(PartnerProfile).where(PartnerProfile.partner_name.in_(DEMO_PARTNER_NAMES))
        )
        self.db.execute(
            delete(ReusableEvidenceBlock).where(
                ReusableEvidenceBlock.block_key == "demo-capability-ai-climate"
            )
        )
        if demo_doc_ids:
            self.db.execute(delete(MemoryChunk).where(MemoryChunk.document_id.in_(demo_doc_ids)))
        self.db.execute(
            delete(MemoryDocument).where(MemoryDocument.title == "Pilot Capability Snapshot")
        )
        self.db.execute(
            delete(DocumentSource).where(DocumentSource.source_uri == DEMO_DOC_SOURCE_URI)
        )
