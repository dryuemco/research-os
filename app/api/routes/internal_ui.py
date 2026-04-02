from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.domain.audit_and_observability.models import AuditEvent
from app.domain.execution_orchestrator.models import ExecutionPlan
from app.domain.institutional_memory.models import ReusableEvidenceBlock
from app.domain.opportunity_discovery.models import Opportunity
from app.domain.proposal_factory.models import Proposal
from app.schemas.export import ExportStateTransitionRequest
from app.services.dashboard_service import DashboardService
from app.services.export_package_service import ExportPackageService
from app.services.memory_service import MemoryService

router = APIRouter()


def _status_badge(status: str) -> str:
    color = {
        "approved": "#127a3f",
        "failed": "#b42318",
        "paused": "#b54708",
        "running": "#175cd3",
        "ready_for_review": "#175cd3",
        "draft": "#667085",
    }.get(status, "#344054")
    style = (
        "padding:2px 8px;border-radius:10px;"
        f"background:{color};color:white;font-size:12px;"
    )
    return f'<span style="{style}">{status}</span>'


def _html_page(title: str, body: str) -> str:
    nav = (
        "<div style='margin-bottom:16px;'>"
        "<a href='/ui'>Home</a> | "
        "<a href='/dashboard/opportunities'>Opportunities API</a> | "
        "<a href='/dashboard/proposals'>Proposals API</a> | "
        "<a href='/memory/exports'>Exports API</a></div>"
    )
    return (
        "<html><head><title>"
        + title
        + "</title></head><body style='font-family:Arial,sans-serif;margin:20px;'>"
        + nav
        + body
        + "</body></html>"
    )


@router.get("", response_class=HTMLResponse)
def internal_dashboard_ui(db: Annotated[Session, Depends(get_db_session)]) -> str:
    summary = DashboardService(db).summary()
    blocks = MemoryService(db).list_blocks(approved_only=False)[:8]
    exports = ExportPackageService(db).list_packages()[:8]

    cards = "".join(
        (
            "<div style='padding:12px;border:1px solid #ddd;border-radius:8px;min-width:140px;'>"
            f"<div style='font-size:12px;color:#667085'>{key}</div>"
            f"<div style='font-size:22px'>{value}</div></div>"
        )
        for key, value in summary.items()
    )

    block_rows = "".join(
        f"<tr><td><a href='/ui/blocks/{b.id}'>{b.block_key}</a></td><td>{b.title}</td>"
        f"<td>{_status_badge(b.approval_status.value)}</td></tr>"
        for b in blocks
    )
    export_rows = "".join(
        f"<tr><td><a href='/ui/exports/{e.id}'>{e.package_name}</a></td>"
        f"<td>{_status_badge(e.status.value)}</td></tr>"
        for e in exports
    )

    body = (
        "<h1>RPOS Internal Operator Dashboard</h1>"
        f"<div style='display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;'>{cards}</div>"
        "<h2>Reusable Memory Blocks</h2>"
        "<table border='1' cellpadding='8' cellspacing='0'>"
        "<tr><th>Key</th><th>Title</th><th>Status</th></tr>"
        f"{block_rows}</table>"
        "<h2 style='margin-top:20px'>Export Packages</h2>"
        "<table border='1' cellpadding='8' cellspacing='0'>"
        "<tr><th>Package</th><th>Status</th></tr>"
        f"{export_rows}</table>"
    )
    return _html_page("RPOS Internal Dashboard", body)


@router.get("/opportunities/{opportunity_id}", response_class=HTMLResponse)
def ui_opportunity_detail(
    opportunity_id: str, db: Annotated[Session, Depends(get_db_session)]
) -> str:
    opp = db.get(Opportunity, opportunity_id)
    if opp is None:
        return _html_page("Opportunity not found", "<h2>Opportunity not found</h2>")
    body = (
        f"<h2>Opportunity: {opp.title}</h2>"
        f"<p><b>State:</b> {opp.state.value}</p><p>{opp.summary}</p>"
        f"<p><b>Deadline:</b> {opp.deadline_at}</p>"
    )
    return _html_page("Opportunity detail", body)


@router.get("/proposals/{proposal_id}", response_class=HTMLResponse)
def ui_proposal_detail(proposal_id: str, db: Annotated[Session, Depends(get_db_session)]) -> str:
    proposal = db.get(Proposal, proposal_id)
    if proposal is None:
        return _html_page("Proposal not found", "<h2>Proposal not found</h2>")
    exports = ExportPackageService(db).list_packages(proposal_id=proposal_id)
    export_links = "".join(
        f"<li><a href='/ui/exports/{item.id}'>{item.package_name}</a> ({item.status.value})</li>"
        for item in exports
    )
    body = (
        f"<h2>Proposal: {proposal.name}</h2><p><b>State:</b> {proposal.state.value}</p>"
        f"<p><b>Human approved for export:</b> {proposal.human_approved_for_export}</p>"
        f"<h3>Linked Export Packages</h3><ul>{export_links}</ul>"
    )
    return _html_page("Proposal detail", body)


@router.get("/exports/{package_id}", response_class=HTMLResponse)
def ui_export_detail(package_id: str, db: Annotated[Session, Depends(get_db_session)]) -> str:
    service = ExportPackageService(db)
    try:
        package = service.get_package(package_id)
        artifacts = service.list_artifacts(package_id)
    except ValueError:
        return _html_page("Export not found", "<h2>Export package not found</h2>")

    artifact_rows = "".join(
        f"<tr><td>{a.artifact_type.value}</td><td>{a.file_name}</td>"
        f"<td><a href='/memory/exports/artifacts/{a.id}/download'>download</a></td></tr>"
        for a in artifacts
    )

    approve_action = ""
    if package.status.value == "ready_for_review":
        approve_action = (
            f"<a href='/ui/exports/{package.id}/approve?actor_id=operator-ui'>"
            "Approve Export Package</a>"
        )

    body = (
        f"<h2>Export Package: {package.package_name}</h2>"
        f"<p>Status: {_status_badge(package.status.value)}</p>"
        f"<p>Proposal ID: <a href='/ui/proposals/{package.proposal_id}'>"
        f"{package.proposal_id}</a></p>"
        f"{approve_action}<h3>Artifacts</h3>"
        "<table border='1' cellpadding='8' cellspacing='0'>"
        "<tr><th>Type</th><th>File</th><th>Link</th></tr>"
        f"{artifact_rows}</table>"
        f"<p><a href='/memory/exports/{package.id}/submission-pack'>"
        "View submission-pack JSON</a></p>"
    )
    return _html_page("Export detail", body)


@router.get("/exports/{package_id}/approve")
def ui_export_approve(
    package_id: str,
    db: Annotated[Session, Depends(get_db_session)],
    actor_id: str = Query(default="operator-ui"),
):
    service = ExportPackageService(db)
    try:
        service.transition_status(
            package_id,
            ExportStateTransitionRequest(target_status="approved", actor_id=actor_id),
        )
        db.commit()
    except ValueError:
        db.rollback()
    return RedirectResponse(url=f"/ui/exports/{package_id}", status_code=303)


@router.get("/audit/{entity_type}/{entity_id}", response_class=HTMLResponse)
def ui_audit_detail(
    entity_type: str,
    entity_id: str,
    db: Annotated[Session, Depends(get_db_session)],
) -> str:
    events = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.entity_type == entity_type, AuditEvent.entity_id == entity_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(100)
    ).all()
    rows = "".join(
        f"<tr><td>{e.created_at}</td><td>{e.event_type}</td><td>{e.actor_id}</td></tr>"
        for e in events
    )
    body = (
        f"<h2>Audit Timeline: {entity_type}/{entity_id}</h2>"
        "<table border='1' cellpadding='8' cellspacing='0'>"
        "<tr><th>When</th><th>Event</th><th>Actor</th></tr>"
        f"{rows}</table>"
    )
    return _html_page("Audit detail", body)


@router.get("/decomposition/{plan_id}", response_class=HTMLResponse)
def ui_decomposition_detail(plan_id: str, db: Annotated[Session, Depends(get_db_session)]) -> str:
    plan = db.get(ExecutionPlan, plan_id)
    if plan is None:
        return _html_page("Plan not found", "<h2>Execution plan not found</h2>")
    body = (
        f"<h2>Execution Plan {plan.plan_name}</h2><p>Status: {plan.state.value}</p>"
        f"<pre>{plan.policy_json}</pre>"
    )
    return _html_page("Decomposition detail", body)


@router.get("/blocks/{block_id}", response_class=HTMLResponse)
def ui_block_detail(block_id: str, db: Annotated[Session, Depends(get_db_session)]) -> str:
    block = db.get(ReusableEvidenceBlock, block_id)
    if block is None:
        return _html_page("Block not found", "<h2>Reusable block not found</h2>")
    body = (
        f"<h2>{block.title}</h2><p>{_status_badge(block.approval_status.value)}</p>"
        f"<pre>{block.body_text}</pre>"
    )
    return _html_page("Reusable block detail", body)
