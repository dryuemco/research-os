from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.services.dashboard_service import DashboardService
from app.services.memory_service import MemoryService

router = APIRouter()


def _status_badge(status: str) -> str:
    color = {
        "approved": "#127a3f",
        "failed": "#b42318",
        "paused": "#b54708",
        "running": "#175cd3",
    }.get(status, "#344054")
    style = (
        "padding:2px 8px;border-radius:10px;"
        f"background:{color};color:white;font-size:12px;"
    )
    return f'<span style="{style}">{status}</span>'


@router.get("", response_class=HTMLResponse)
def internal_dashboard_ui(db: Annotated[Session, Depends(get_db_session)]) -> str:
    summary = DashboardService(db).summary()
    blocks = MemoryService(db).list_blocks(approved_only=False)[:10]

    block_rows = "".join(
        (
            f"<tr><td>{b.block_key}</td><td>{b.title}</td>"
            f"<td>{_status_badge(b.approval_status.value)}</td></tr>"
        )
        for b in blocks
    )

    cards = "".join(
        (
            "<div style='padding:12px;border:1px solid #ddd;"
            "border-radius:8px;min-width:140px;'>"
            f"<div style='font-size:12px;color:#667085'>{key}</div>"
            f"<div style='font-size:22px'>{value}</div></div>"
        )
        for key, value in summary.items()
    )

    return f"""
    <html>
      <head><title>RPOS Internal Dashboard</title></head>
      <body style='font-family:Arial,sans-serif;margin:20px;'>
        <h1>RPOS Internal Operator Dashboard</h1>
        <p>Inspection and workflow visibility layer.</p>
        <div style='display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;'>{cards}</div>
        <h2>Reusable Memory Blocks</h2>
        <table border='1' cellpadding='8' cellspacing='0'>
          <tr><th>Key</th><th>Title</th><th>Approval</th></tr>
          {block_rows}
        </table>
        <p style='margin-top:16px'>API feeds: <code>/dashboard/*</code>, <code>/memory/*</code>.</p>
      </body>
    </html>
    """
