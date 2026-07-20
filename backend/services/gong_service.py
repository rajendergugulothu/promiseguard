"""
Gong integration service.
Pulls transcripts from Gong API and submits them for extraction.

Gong API: https://us-67939.api.gong.io/v2/
Auth: OAuth 2.0 client credentials or Access Key + Secret
"""

import os
import httpx
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from models.source import Source, SourceType
from services.extractor import extract_commitments

GONG_BASE = "https://us-67939.api.gong.io/v2"


def _gong_headers() -> dict:
    client_id = os.getenv("GONG_CLIENT_ID", "")
    client_secret = os.getenv("GONG_CLIENT_SECRET", "")
    import base64
    token = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


async def pull_recent_transcripts(
    db: AsyncSession,
    workspace_id: str,
    account_id: str,
    account_name: str,
    days_back: int = 30,
) -> list[Source]:
    """Pull call transcripts from Gong for the last N days."""
    from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")

    async with httpx.AsyncClient(timeout=30) as client:
        # List calls
        calls_resp = await client.post(
            f"{GONG_BASE}/calls/extensive",
            headers=_gong_headers(),
            json={
                "filter": {
                    "fromDateTime": from_date,
                    "toDateTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            },
        )
        if calls_resp.status_code != 200:
            raise ValueError(f"Gong API error: {calls_resp.status_code} {calls_resp.text[:200]}")

        calls = calls_resp.json().get("calls", [])
        call_ids = [c["metaData"]["id"] for c in calls][:10]  # limit to 10 most recent

        if not call_ids:
            return []

        # Pull transcripts
        trans_resp = await client.post(
            f"{GONG_BASE}/calls/transcript",
            headers=_gong_headers(),
            json={"filter": {"callIds": call_ids}},
        )
        if trans_resp.status_code != 200:
            raise ValueError(f"Gong transcript error: {trans_resp.status_code}")

        transcripts = trans_resp.json().get("callTranscripts", [])

    sources = []
    for transcript in transcripts:
        # Build speaker-labeled text
        sentences = transcript.get("transcript", [])
        text_parts = []
        for s in sentences:
            speaker = s.get("speakerName", "Speaker")
            text = s.get("sentences", [{}])[0].get("text", "")
            if text:
                text_parts.append(f"{speaker}: {text}")

        full_text = "\n".join(text_parts)
        if not full_text.strip():
            continue

        call_id = transcript.get("callId", "")
        source = Source(
            workspace_id=workspace_id,
            account_id=account_id,
            account_name=account_name,
            source_type=SourceType.gong_transcript,
            title=f"Gong call {call_id[:8]}",
            uploaded_by="gong-integration",
            raw_text=full_text,
            metadata_={"gong_call_id": call_id},
        )
        db.add(source)
        await db.flush()

        await extract_commitments(db, str(source.id))
        sources.append(source)

    return sources
