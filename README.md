<div align="center">

  <h1>PromiseGuard</h1>

  <p><strong>AI-powered commitment intelligence for B2B SaaS sales and delivery teams.</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=nextdotjs" />
    <img src="https://img.shields.io/badge/FastAPI-Python_3.12-009688?style=flat-square&logo=fastapi" />
    <img src="https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=flat-square&logo=postgresql" />
    <img src="https://img.shields.io/badge/Claude-Anthropic-cc785c?style=flat-square&logo=anthropic" />
    <img src="https://img.shields.io/badge/Clerk-Auth-6C47FF?style=flat-square&logo=clerk" />
    <img src="https://img.shields.io/badge/TypeScript-5-3178c6?style=flat-square&logo=typescript" />
  </p>

</div>

---

## What is PromiseGuard?

B2B SaaS companies make commitments to customers across sales calls, emails, contracts, and implementation meetings. These commitments lack structured owners, due dates, and links to product capability. When they are missed, the result is escalations, churn, and revenue loss. **PromiseGuard ingests transcripts, emails, and contracts, extracts every commitment using an LLM that distinguishes promises from possibilities, routes candidates through an AE review gate before they enter the ledger, and surfaces risk before the customer discovers the gap.**

> **Commitment made. Context captured. Risk scored. Nothing falls through.**

---

## How It Works

```
  Transcript, email, contract, or implementation note ingested
              │
              ▼
  LLM Extraction ── Claude classifies each statement as ───────────────
              │      commitment / possibility / description / aspiration  │
              │      Only commitments proceed                             │
              │                                                           │
              ▼                                                           │
  AE Review Gate ── candidates surface to the AE before the ledger      │
              │      confirm · edit · dismiss                             │
              │      No commitment is created without AE sign-off        │
              │                                                           │
              ▼                                                           │
  Legal Gate ─── security_compliance tier → legal review queue          │
              │    CHECK constraint at DB level — cannot be bypassed     │
              │                                                           │
              ▼                                                           │
  Capability Matching ── pgvector semantic match to product catalogue    │
              │            current · on_roadmap · unsupported · unknown  │
              │                                                           │
              ▼                                                           │
  Conflict Detection ── cross-customer · cross-document ·               │
              │           date-infeasible · self-contradiction           │
              │                                                           │
              ▼                                                           │
  Risk Scoring ─── composite: severity × urgency × feasibility          │
              │      × ARR exposure · recomputes on every state change   │
              │                                                           │
              ▼                                                           │
  Five views: QBR prep · portfolio risk · account history ──────────────┘
              commitment handoff report · PM portfolio view
```

---

## Key Features

- 🧠 **Four-Class Extraction** — Claude distinguishes commitments from possibilities, descriptions, and aspirations; the concierge test found 4 of 6 false positives were "we should be able to" statements, so the system prompt includes concrete examples of each class
- 🔒 **AE Review Gate** — every extracted candidate surfaces to the AE before entering the ledger; enforced at the data layer via a CHECK constraint that blocks pending candidates from having a `commitment_id`
- ⚖️ **Legal Review Queue** — security and compliance commitments cannot have `legal_review_status = not_required`; enforced as a database-level CHECK constraint, not an application convention
- 🔍 **pgvector Capability Matching** — commitment statements are embedded and matched against the product capability registry; four-state output: current / on_roadmap / unsupported / unknown; `unknown` and `unsupported` are never collapsed
- ⚠️ **Conflict Detection** — four conflict types: cross-customer, cross-document, date-infeasible, self-contradiction; runs after every AE confirmation
- 📊 **Composite Risk Scoring** — severity × urgency × feasibility × ARR exposure; recomputes as a background task on every status change, capability match update, new conflict, or due-date change
- 📋 **Five Reporting Views** — QBR prep, CCO portfolio dashboard, account history, commitment handoff report, PM portfolio view
- 🔗 **Gong + Salesforce + Slack ingestion** — live integrations are the primary flow; file upload is the fallback

---

## Tech Stack

**Backend** — FastAPI · SQLAlchemy 2.0 async · asyncpg · pgvector · PostgreSQL 16 (Neon) · Anthropic Claude (extraction, conflict detection, risk explanation) · OpenAI text-embedding-3-small (capability matching)

**Frontend** — Next.js 14 (App Router) · TypeScript · Tailwind CSS · Clerk v5

**Infrastructure** — Neon (hosted Postgres + pgvector) · Render (backend) · Vercel (frontend) · Docker Compose (local dev)

---

## Design Decisions

**Two separate tables for candidates and commitments.** Pre-AE and post-AE data are kept entirely separate. A single table with a status field creates the risk of application code accidentally promoting candidates to commitments. The two-table design makes that structurally impossible.

**The AE gate is enforced at three layers.** `verdict` defaults to `pending`. A CHECK constraint prevents any `pending` candidate from having a `commitment_id`. The candidates router is the only code path that creates Commitment records, and only after an explicit confirm or edit. No other router imports Commitment creation logic.

**The legal gate is a CHECK constraint, not application logic.** `commitment_type = 'security_compliance'` AND `legal_review_status = 'not_required'` is rejected at the database level. A bug, a missing condition, or a future developer skipping the service layer cannot bypass it.

**`unknown` ≠ `unsupported` in capability matching.** The capability match has four states. `unknown` means no match was found above the similarity threshold or roadmap data is incomplete. `unsupported` means a matching capability exists and is explicitly not planned. Collapsing them generates false-positive risk flags on capabilities that simply haven't been catalogued yet.

**Risk scores recompute continuously, not on a schedule.** Triggered as background tasks on: status change, capability match update, due date change, new conflict detected. A score that is even a few hours stale can under-represent a commitment that just had its roadmap date slip.

**Possibility language is the hardest extraction problem.** "We should be able to get that done by Q3" is not a commitment. A concierge test on sales transcript data found that 4 of 6 false positives were phrased as possibilities. The extraction system prompt includes concrete labelled examples of all four classes and explicitly instructs the model not to extract possibility language.

---

## Research and Evaluation Context

PromiseGuard was developed as an AI Product Management portfolio project using secondary research, structured persona simulations, and a controlled feasibility evaluation on synthetic sales transcript data. The current implementation demonstrates product feasibility, AI pipeline design, and full-stack execution. It has not yet been validated with production customers, live enterprise sales teams, or confirmed design partners.

---

## Portfolio Context

PromiseGuard is the third project in an AI operations portfolio covering the full agent and customer lifecycle.

| | PolicyLens AI | ExceptionLoop | PromiseGuard |
|--|--------------|---------------|--------------|
| **When** | Before deployment | After deployment | Sales to delivery |
| **What** | Tests agents against policy | Manages escalations + learns from them | Tracks every customer promise |
| **Output** | Launch-readiness report | Automation pipeline | Risk-scored commitment ledger |
| **North Star** | % critical policy rules tested before prod | % recurring exceptions converted to automation | % commitments with owner, due date, and capability link before go-live |

---

## About

PromiseGuard is a deployed, production-oriented portfolio MVP demonstrating:

- LLM-powered commitment extraction with four-class taxonomy
- Multi-layer AE review gate enforced at the data layer
- Database-level legal gate via CHECK constraint
- pgvector semantic capability matching with four-state output
- Deterministic conflict detection across four conflict types
- Composite risk scoring with continuous recomputation
- Gong, Salesforce, and Slack ingestion integrations
- Authenticated full-stack deployment with Clerk v5

The project was built to demonstrate how commitments made across the sales and delivery lifecycle can be captured, classified, linked to product capability, and surfaced as risk before they become customer escalations.

**Built by [Rajender Gugulothu](https://github.com/rajendergugulothu)**

---

<div align="center">
  <em>PromiseGuard — Every promise tracked. Every risk surfaced.</em>
</div>
