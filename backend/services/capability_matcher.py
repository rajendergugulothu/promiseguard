"""
Capability matcher — semantic match from commitment statement to capability registry.

CRITICAL: unknown != unsupported.
- unknown: no capability matched above threshold OR roadmap data incomplete
- unsupported: matching capability exists and is explicitly not planned

Threshold: 0.75 cosine similarity for a match attempt.
Below threshold → status=unknown, not status=unsupported.
"""

import os
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from models.commitment import Commitment
from models.capability import CapabilityRegistry, CapabilityMatch, CapabilityStatus
from models.audit import AuditLog

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "placeholder"))
MATCH_THRESHOLD = 0.75
EMBEDDING_MODEL = "text-embedding-3-small"


async def embed_text(text_input: str) -> list[float]:
    response = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text_input,
    )
    return response.data[0].embedding


async def match_capability(
    db: AsyncSession,
    commitment_id: str,
) -> CapabilityMatch:
    """
    Find the best capability match for a commitment.
    Returns a CapabilityMatch with one of four statuses:
      current | on_roadmap | unsupported | unknown
    unknown is returned when no match exceeds threshold OR data is incomplete.
    """
    result = await db.execute(select(Commitment).where(Commitment.id == commitment_id))
    commitment = result.scalar_one_or_none()
    if not commitment:
        raise ValueError(f"Commitment {commitment_id} not found.")

    embedding = await embed_text(commitment.statement)

    # pgvector similarity search
    rows = await db.execute(
        text("""
            SELECT id, name, status, roadmap_date, roadmap_confidence,
                   1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM capability_registry
            WHERE workspace_id = :workspace_id
              AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT 1
        """),
        {"embedding": str(embedding), "workspace_id": str(commitment.workspace_id)},
    )
    row = rows.fetchone()

    if not row or row.similarity < MATCH_THRESHOLD:
        # No match above threshold → unknown (NOT unsupported)
        match = CapabilityMatch(
            commitment_id=commitment.id,
            capability_id=None,
            match_status=CapabilityStatus.unknown,
            similarity_score=float(row.similarity) if row else None,
            matched_by="system",
            match_notes="No capability matched above similarity threshold. Status is unknown, not unsupported.",
        )
    else:
        cap_status = CapabilityStatus(row.status)
        roadmap_date = row.roadmap_date

        # If on_roadmap but no roadmap date → unknown (data incomplete)
        if cap_status == CapabilityStatus.on_roadmap and not roadmap_date:
            match = CapabilityMatch(
                commitment_id=commitment.id,
                capability_id=row.id,
                match_status=CapabilityStatus.unknown,
                similarity_score=float(row.similarity),
                roadmap_date=None,
                matched_by="system",
                match_notes=f"Matched capability '{row.name}' (on_roadmap) but roadmap date is missing. Status is unknown.",
            )
        else:
            match = CapabilityMatch(
                commitment_id=commitment.id,
                capability_id=row.id,
                match_status=cap_status,
                similarity_score=float(row.similarity),
                roadmap_date=roadmap_date,
                matched_by="system",
            )

    db.add(match)
    await db.flush()  # populate match.id before referencing it in AuditLog
    db.add(AuditLog(
        workspace_id=commitment.workspace_id,
        entity_type="capability_match",
        entity_id=match.id,
        action="capability_matched",
        actor="system",
        new_value={"status": match.match_status.value, "similarity": match.similarity_score},
    ))

    return match
