"""
Commitment extractor.

The hardest problem: distinguishing a commitment from a possibility,
a description, and an aspiration. The concierge test found 4 of 6
false positives were "we should be able to" statements. The system
prompt must make this distinction explicit with concrete examples.

Creates commitment_candidates with verdict='pending'.
NEVER creates Commitment records — that is the AE review gate's job.
"""

import json
import re
import os
from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.source import Source
from models.candidate import CommitmentCandidate, CandidateVerdict, CommitmentType, SeverityTier
from models.audit import AuditLog

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

EXTRACT_SYSTEM = """You are PromiseGuard, an AI commitment extraction engine for B2B SaaS companies.

Your job is to identify genuine customer commitments made by sellers or implementation teams.

CRITICAL: You must distinguish between four classes of statement:

CLASS 1 — COMMITMENT (extract these)
A commitment is an explicit promise with a specific promisor about a specific outcome.
Examples:
- "We will have that integration ready by Q3." → COMMITMENT
- "I'll make sure the data stays in the EU." → COMMITMENT
- "You'll get a dedicated implementation manager." → COMMITMENT
- "We're committed to delivering the migration before your go-live." → COMMITMENT
- "That will be included in your contract at no extra cost." → COMMITMENT

CLASS 2 — POSSIBILITY (do NOT extract)
Possibility language is conditional or exploratory. It is NOT a promise.
Examples:
- "We should be able to get that done by Q3." → POSSIBILITY
- "We could look at including that." → POSSIBILITY
- "That might be something we can support." → POSSIBILITY
- "I think we can probably do that." → POSSIBILITY
- "We'd consider that as part of the deal." → POSSIBILITY

CLASS 3 — DESCRIPTION (do NOT extract)
A description of existing product capability. Not a promise about the future.
Examples:
- "Our platform supports SSO." → DESCRIPTION
- "We have a native Salesforce integration." → DESCRIPTION
- "The API can handle that use case." → DESCRIPTION

CLASS 4 — ASPIRATION (do NOT extract)
Directional intent without a specific commitment or timeline.
Examples:
- "We're working towards that." → ASPIRATION
- "That's on our roadmap." → ASPIRATION
- "We're planning to support that in the future." → ASPIRATION

For each COMMITMENT found, classify severity:
- critical: legal obligation, data residency, compliance, SLA breach risk
- high: feature delivery, go-live dates, pricing locked
- medium: support level, access level, reporting
- low: nice-to-have inclusions, minor process commitments

Return ONLY a JSON array. No markdown. No backticks. Empty array if no commitments found.

[
  {
    "raw_statement": "normalised promise statement",
    "evidence_passage": "exact quote from the source text",
    "evidence_location": "timestamp, page, or speaker label",
    "commitment_type": "feature|date|pricing|security_compliance|performance|sla|custom|other",
    "severity_tier": "critical|high|medium|low",
    "promisor": "name of person who made the promise or null",
    "counterparty": "customer contact it was made to or null",
    "raw_due_date": "date as stated in source or null",
    "confidence": 0.0,
    "classification_reason": "one sentence: why this is a commitment, not a possibility"
  }
]"""


async def extract_commitments(
    db: AsyncSession,
    source_id: str,
) -> list[CommitmentCandidate]:
    """
    Extract commitment candidates from a source document.
    Creates CommitmentCandidate records with verdict='pending'.
    Does NOT create Commitment records.
    """
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise ValueError(f"Source {source_id} not found.")
    if not source.raw_text:
        raise ValueError(f"Source {source_id} has no raw text to extract from.")

    # Chunk long documents — Claude can handle large contexts but chunking
    # improves extraction precision for very long transcripts
    text = source.raw_text
    chunks = _chunk_text(text, max_chars=15000)

    all_candidates = []
    for chunk in chunks:
        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=EXTRACT_SYSTEM,
            messages=[{"role": "user", "content": f"Extract all commitments from this source:\n\n{chunk}"}],
        )
        raw = message.content[0].text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            items = json.loads(raw)
        except json.JSONDecodeError:
            items = []

        for item in items:
            candidate = CommitmentCandidate(
                source_id=source.id,
                workspace_id=source.workspace_id,
                raw_statement=item.get("raw_statement", ""),
                evidence_passage=item.get("evidence_passage", ""),
                evidence_location=item.get("evidence_location"),
                commitment_type=_safe_enum(CommitmentType, item.get("commitment_type"), CommitmentType.other),
                severity_tier=_safe_enum(SeverityTier, item.get("severity_tier"), SeverityTier.medium),
                promisor=item.get("promisor"),
                counterparty=item.get("counterparty"),
                raw_due_date=item.get("raw_due_date"),
                extraction_confidence=float(item.get("confidence", 0.5)),
                classification_reason=item.get("classification_reason"),
                verdict=CandidateVerdict.pending,  # always pending — AE gate enforces this
            )
            db.add(candidate)
            all_candidates.append(candidate)

    await db.flush()

    # Update source processed_at
    from datetime import datetime, timezone
    source.processed_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        workspace_id=source.workspace_id,
        entity_type="source",
        entity_id=source.id,
        action="extraction_complete",
        actor="system",
        new_value={"candidates_created": len(all_candidates)},
    ))

    return all_candidates


def _chunk_text(text: str, max_chars: int = 15000) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks, current = [], []
    current_len = 0
    for para in text.split("\n\n"):
        if current_len + len(para) > max_chars and current:
            chunks.append("\n\n".join(current))
            current, current_len = [], 0
        current.append(para)
        current_len += len(para)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _safe_enum(enum_class, value, default):
    try:
        return enum_class(value)
    except (ValueError, KeyError):
        return default
