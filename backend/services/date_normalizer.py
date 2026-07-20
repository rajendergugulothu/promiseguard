"""
Temporal extraction + confidence labeling.
Four cases: explicit, relative, conditional, none.
"""

import json, re, os
from datetime import date
from anthropic import AsyncAnthropic
from models.commitment import DateConfidence

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

DATE_SYSTEM = """Extract and normalize a due date from raw date text.
Return ONLY valid JSON: {"iso_date": "YYYY-MM-DD or null", "confidence": "confirmed|inferred|unknown", "note": "brief explanation"}

Rules:
- Explicit date ("March 31", "Q3 2026 end") → iso_date + confidence=confirmed
- Relative date ("end of Q3", "next quarter") → infer ISO date + confidence=inferred
- Conditional ("before go-live", "at contract signing") → iso_date=null + confidence=unknown
- No date → iso_date=null + confidence=unknown

Today's reference date: assume current date is July 2026 unless context suggests otherwise."""


async def normalize_date(raw_date_text: str | None) -> tuple[date | None, DateConfidence]:
    if not raw_date_text or raw_date_text.strip() == "":
        return None, DateConfidence.unknown

    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=DATE_SYSTEM,
        messages=[{"role": "user", "content": f"Raw date text: {raw_date_text}"}],
    )
    raw = message.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
        iso = data.get("iso_date")
        conf = DateConfidence(data.get("confidence", "unknown"))
        parsed = date.fromisoformat(iso) if iso else None
        return parsed, conf
    except Exception:
        return None, DateConfidence.unknown
