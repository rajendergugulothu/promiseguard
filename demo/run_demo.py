"""
PromiseGuard — End-to-End Demo Script

Simulates the full commitment intelligence loop using realistic
B2B SaaS sales and implementation artefacts.

Usage: python demo/run_demo.py
Requires: uvicorn main:app running at http://localhost:8000
"""

import asyncio
import httpx
import json

BASE = "http://localhost:8000"
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; B = "\033[94m"; W = "\033[97m"; M = "\033[0m"

def ok(m): print(f"{G}  ✓ {m}{M}")
def info(m): print(f"    {m}")
def head(m): print(f"\n{W}{'─'*60}{M}\n{B}{m}{M}")
def warn(m): print(f"{Y}  ⚠ {m}{M}")

# Realistic Nexora sales transcript with mixed commitment types
NEXORA_TRANSCRIPT = """
Jordan: Thanks for joining. I want to make sure we're aligned on what we can deliver before you sign.

Rafael: Absolutely. The main things we need confirmed are the Salesforce integration, the EU data residency requirement, and the Q3 go-live date.

Jordan: The Salesforce integration will be ready before your go-live. That's a standard integration we've shipped for 15 customers. 
We will have it configured and tested in your environment by July 31st.

Rafael: And data residency?

Jordan: I can confirm your data will remain in our EU region only. We do not replicate to US-East. 
I'll make sure that's documented in the contract.

Rafael: What about the custom migration tool? Our ops team mentioned they'd need something to handle the legacy data format.

Jordan: That's something we could potentially build as part of the implementation. I'd need to check with the engineering team on timeline, 
but we should be able to include that in your onboarding package.

Rafael: And the dedicated implementation manager — that was mentioned in the proposal.

Jordan: Yes, you'll have a dedicated implementation manager from day one of the project. 
That's included in your enterprise tier.

Rafael: Okay. And we need the dashboard reporting feature ready by Q3. Our board reviews in October.

Jordan: The dashboard is on our roadmap and we're aiming to ship it in Q3. I'm confident you'll have it for your October review.
"""

BUILDRIGHT_TRANSCRIPT = """
Priya: Welcome to the Buildright kickoff. I want to make sure I understand everything that was promised during the sales process.

Customer: The sales team mentioned we'd have a dedicated Slack channel for implementation support.

Priya: Yes, I can confirm we'll set up a dedicated Slack channel within the first 24 hours. 
You'll have direct access to me and the technical team.

Customer: And the go-live date was confirmed as September 15th?

Priya: We're targeting September 15th for go-live. I'll make sure that date is in the project plan.
That gives us 10 weeks from today.

Customer: What about the API rate limits? Sales said we'd get enterprise limits.

Priya: You're on the enterprise tier, so your API rate limit is 10,000 requests per hour. 
That's confirmed in your contract.
"""


async def run():
    async with httpx.AsyncClient(timeout=60) as client:

        head("Step 1 — Health check")
        r = await client.get(f"{BASE}/health")
        if r.status_code != 200:
            print(f"{R}API not responding. Start with: uvicorn main:app --reload{M}"); return
        ok(f"API running: {r.json()['service']} v{r.json()['version']}")

        head("Step 2 — Create workspace")
        r = await client.post(f"{BASE}/workspaces/", json={
            "name": "Enterprise Sales — Q3 2026", "organisation": "Nexora Inc", "created_by": "demo"
        })
        ws = r.json(); ws_id = ws["id"]
        ok(f"Workspace: {ws['name']} ({ws_id[:8]}…)")

        head("Step 3 — Seed capability registry")
        caps = [
            {"name": "Salesforce Integration", "description": "Native Salesforce CRM integration with bidirectional sync", "status": "current"},
            {"name": "EU Data Residency", "description": "EU-only data storage with no cross-region replication", "status": "current"},
            {"name": "Dashboard Reporting", "description": "Executive dashboard with custom report builder", "status": "on_roadmap", "roadmap_date": "2026-09-30"},
            {"name": "Custom Data Migration Tool", "description": "Bespoke migration tooling for legacy data formats", "status": "unsupported"},
            {"name": "Dedicated Implementation Manager", "description": "Named implementation manager for enterprise accounts", "status": "current"},
        ]
        for cap in caps:
            r = await client.post(f"{BASE}/workspaces/{ws_id}/capabilities", json=cap)
            info(f"  Capability: {cap['name']} [{cap['status']}]")
        ok(f"5 capabilities seeded")

        head("Step 4 — Ingest source documents")
        sources = [
            {"account_id": "NEXORA-001", "account_name": "Nexora Inc",
             "source_type": "gong_transcript", "title": "Nexora Sales Call — July 2026",
             "uploaded_by": "jordan.marsh@scaleops.com", "raw_text": NEXORA_TRANSCRIPT},
            {"account_id": "BUILDRIGHT-001", "account_name": "Buildright Corp",
             "source_type": "gong_transcript", "title": "Buildright Kickoff — July 2026",
             "uploaded_by": "priya.s@buildfast.com", "raw_text": BUILDRIGHT_TRANSCRIPT},
        ]
        all_candidates = 0
        for s in sources:
            r = await client.post(f"{BASE}/sources/ingest", json={"workspace_id": ws_id, **s})
            result = r.json()
            info(f"  {s['account_name']}: {result['candidates_created']} candidates extracted")
            all_candidates += result["candidates_created"]
        ok(f"Total: {all_candidates} commitment candidates pending AE review")

        head("Step 5 — AE review gate")
        r = await client.get(f"{BASE}/workspaces/{ws_id}/candidates")
        candidates = r.json()
        info(f"  {len(candidates)} candidates in queue")

        confirmed_count = dismissed_count = 0
        for c in candidates:
            # Dismiss "should be able to" possibilities, confirm clear commitments
            is_possibility = any(p in c["raw_statement"].lower() for p in ["should be able", "could", "potentially", "aiming"])
            if is_possibility:
                await client.post(f"{BASE}/candidates/{c['id']}/review", json={
                    "verdict": "dismissed",
                    "reviewed_by": "jordan.marsh@scaleops.com",
                    "dismiss_reason": "Possibility/aspiration language — not a genuine commitment",
                })
                dismissed_count += 1
            else:
                await client.post(f"{BASE}/candidates/{c['id']}/review", json={
                    "verdict": "confirmed",
                    "reviewed_by": "jordan.marsh@scaleops.com",
                    "responsible_owner": "jordan.marsh@scaleops.com",
                    "arr_exposure": 180000 if "nexora" in c.get("counterparty", "").lower() else 95000,
                })
                confirmed_count += 1

        ok(f"AE review complete: {confirmed_count} confirmed, {dismissed_count} dismissed")

        head("Step 6 — Check legal queue")
        r = await client.get(f"{BASE}/workspaces/{ws_id}/legal-queue")
        legal = r.json()
        if legal:
            warn(f"{len(legal)} commitment(s) routed to legal review (security/compliance tier)")
            for lr in legal:
                info(f"  Review ID: {lr['id'][:8]}… — status: {lr['status']}")
                await client.post(f"{BASE}/legal-reviews/{lr['id']}/adjudicate", json={
                    "reviewer": "legal@nexora.com",
                    "decision": "approved",
                    "notes": "EU data residency confirmed. Added to DPA.",
                })
            ok("Legal reviews adjudicated")
        else:
            ok("No legal review items")

        head("Step 7 — Check conflicts detected")
        r = await client.get(f"{BASE}/workspaces/{ws_id}/conflicts")
        conflicts = r.json()
        ok(f"{len(conflicts)} conflict(s) detected")
        for c in conflicts:
            warn(f"  [{c['conflict_type']}] {c['description'][:80]}")

        head("Step 8 — Portfolio risk dashboard (CCO view)")
        r = await client.get(f"{BASE}/workspaces/{ws_id}/portfolio")
        portfolio = r.json()
        ok(f"Portfolio: {portfolio['total_open_commitments']} open commitments")
        info(f"  Total ARR exposure: ${portfolio['total_arr_exposure']:,.0f}")
        for acct in portfolio.get("accounts", []):
            info(f"  {acct['account_name']}: {acct['total_commitments']} commitments · ${acct['total_arr_exposure']:,.0f} ARR · {acct['unowned']} unowned")

        head("Step 9 — QBR prep view (CSM view for Nexora)")
        r = await client.get(f"{BASE}/accounts/NEXORA-001/qbr-view?workspace_id={ws_id}")
        qbr = r.json()
        ok(f"QBR prep: {qbr['total']} commitments")
        info(f"  Overdue: {qbr['overdue']} · Unowned: {qbr['unowned']} · With conflicts: {qbr['with_open_conflicts']}")

        head("Step 10 — Handoff report (IM view for Buildright)")
        r = await client.get(f"{BASE}/accounts/BUILDRIGHT-001/handoff-report?workspace_id={ws_id}")
        handoff = r.json()
        ok(f"Handoff report: {handoff['total_commitments']} commitments")
        info(f"  Unowned: {handoff['summary']['unowned']}")
        info(f"  Pending legal: {handoff['summary']['pending_legal_review']}")
        info(f"  Unsupported capability: {handoff['summary']['unsupported_capability']}")

        head("Demo complete — summary")
        print(f"""
  {G}Source documents ingested:{M}      2
  {G}Commitment candidates extracted:{M} {all_candidates}
  {G}Confirmed by AE:{M}                {confirmed_count}
  {G}Dismissed by AE:{M}                {dismissed_count}
  {G}Legal reviews created:{M}          {len(legal)}
  {G}Conflicts detected:{M}             {len(conflicts)}
  {G}Accounts in portfolio:{M}          {len(portfolio.get('accounts', []))}
  
  This is what PromiseGuard does for a CS team every week:
  Calls ingested → commitments extracted → AE reviews → legal gate
  → capability matched → conflicts surfaced → portfolio risk visible
  → CSMs walk into QBRs prepared → IMs know what was promised at kickoff
""")


if __name__ == "__main__":
    asyncio.run(run())
