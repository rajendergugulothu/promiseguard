<div align="center">

  <h1>PromiseGuard</h1>

  <p><strong>AI-powered commitment intelligence for B2B SaaS sales and delivery teams.</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=nextdotjs" />
    <img src="https://img.shields.io/badge/FastAPI-Python_3.11-009688?style=flat-square&logo=fastapi" />
    <img src="https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=flat-square&logo=postgresql" />
    <img src="https://img.shields.io/badge/Claude-Anthropic-cc785c?style=flat-square&logo=anthropic" />
    <img src="https://img.shields.io/badge/Clerk-Auth-6C47FF?style=flat-square&logo=clerk" />
    <img src="https://img.shields.io/badge/TypeScript-5-3178c6?style=flat-square&logo=typescript" />
  </p>

</div>

---

## What is PromiseGuard?

B2B SaaS companies make commitments to customers across sales calls, emails, contracts, and implementation meetings. These commitments lack structured owners, due dates, and links to product capability. When they are missed, the result is escalations, churn, and revenue loss.

**PromiseGuard ingests transcripts, emails, contracts, and implementation notes; extracts candidate commitments while distinguishing promises from possibilities; routes candidates through a human review gate; and surfaces potential delivery risk before it becomes a customer escalation.**

> **Commitment made. Context captured. Risk surfaced.**

---

## How It Works

```
  Transcript, email, contract, or implementation note ingested
              │
              ▼
  LLM Extraction ── Claude classifies each statement as ───────────────
              │      commitment / possibility / description / aspiration  │
              │      Only commitment candidates proceed                   │
              │                                                           │
              ▼                                                           │
  Human Review Gate ── candidates surface to the authorized reviewer    │
              │      (AE, CSM, solution engineer, delivery lead)         │
              │      confirm · edit · dismiss — all actions audited      │
              │      No commitment enters the ledger without review      │
              │                                                           │
              ▼                                                           │
  Legal-Sensitive Queue ── configurable categories route to legal       │
              │    CHECK constraint at DB layer for the modeled workflow  │
              │                                                           │
              ▼                                                           │
  Capability Matching ── pgvector semantic match to product catalogue   │
              │            current · on_roadmap · unsupported · unknown  │
              │            unknown ≠ unsupported — never collapsed       │
              │                                                           │
              ▼                                                           │
  Hybrid Conflict Detection ── deterministic checks for date and        │
              │    state inconsistencies; AI-assisted analysis for        │
              │    cross-document, cross-customer, and self-contradictory │
              │    patterns — surfaced as conflict candidates for review  │
              │                                                           │
              ▼                                                           │
  Heuristic Risk Scoring ── severity × urgency × feasibility            │
              │      × account exposure · recomputes on every change     │
              │                                                           │
              ▼                                                           │
  Five views: QBR prep · portfolio risk · account history ──────────────┘
              commitment handoff · PM demand view
```

---

## Key Features

- 🧠 **Four-Class Candidate Extraction** — Claude classifies statements as commitments, possibilities, descriptions, or aspirations and surfaces only commitment candidates for human review; in a manually constructed synthetic evaluation, four of six observed false positives involved possibility language ("we should be able to"), which informed the extraction taxonomy and prompt examples
- 🔒 **Human Review Gate** — candidates must be confirmed, edited, or dismissed by an authorized reviewer before entering the commitment ledger; dismissed candidates are retained with reason, reviewer identity, timestamp, and source evidence for audit history
- ⚖️ **Legal-Sensitive Review Queue** — commitment categories requiring legal scrutiny route to a legal review queue; enforced at the database layer for the modeled workflow state
- 🔍 **Capability Matching** — semantic matching links confirmed commitments to current, roadmap, unsupported, or unknown capability states; `unknown` and `unsupported` are never collapsed
- ⚠️ **Hybrid Conflict Detection** — deterministic checks identify date and state inconsistencies; AI-assisted analysis surfaces potential cross-document, cross-customer, and self-contradictory commitments as conflict candidates for human review
- 📊 **Heuristic Risk Scoring** — transparent composite score combining severity, urgency, capability feasibility, conflict status, and account exposure; recomputes on every state change
- 📋 **Five Operational Views** — QBR preparation, CCO portfolio dashboard, account history, commitment handoff report, PM product-demand view
- 🔗 **Integration-Ready Ingestion** — adapters designed for Gong, Salesforce, and Slack ingestion workflows, with file upload available for controlled evaluation

---

## Tech Stack

**Backend** — FastAPI · SQLAlchemy 2.0 async · asyncpg · pgvector · PostgreSQL 16 (Neon) · Anthropic Claude (extraction, conflict analysis, date normalization) · OpenAI text-embedding-3-small (capability matching)

**Frontend** — Next.js 14 (App Router) · TypeScript · Tailwind CSS · Clerk v5

**Infrastructure** — Neon (hosted Postgres + pgvector) · Render (backend) · Vercel (frontend) · Docker Compose (local dev)

---

## Design Decisions

**Two separate tables for candidates and commitments.** Pre-review and post-review data are kept entirely separate. The two-table design isolates unreviewed candidates from confirmed commitments and reduces the risk of accidental promotion through normal application flows. Workflow constraints are enforced beyond the interface at the service and database layers.

**The human review gate is enforced at three layers.** `verdict` defaults to `pending`. A CHECK constraint prevents any `pending` candidate from having a `commitment_id`. The candidates router is the only code path that creates Commitment records. Dismissed candidates are retained with full audit history — dismissal reason, reviewer identity, timestamp, and original source evidence — so inconvenient commitments cannot be removed without a visible record.

**The reviewer is not always the AE.** An AE may have incentives to confirm, soften, or dismiss commitments. Commitments originate from CSMs, solution engineers, executives, legal teams, and delivery leads. The system routes candidates to the responsible reviewer based on source and commitment type rather than defaulting to the AE in all cases.

**Legal classification is designed to be configurable.** The current implementation triggers legal review for security and compliance commitments. Pricing, data residency, SLA guarantees, regulatory representations, custom contract terms, and roadmap promises are equally legally sensitive in production contexts. The architecture is designed around a configurable `legal_sensitive` classification rather than a single hardcoded type.

**`unknown` ≠ `unsupported` in capability matching.** The capability match has four states. `unknown` means no match was found above the similarity threshold or roadmap data is incomplete. `unsupported` means a matching capability exists and is explicitly not planned. Collapsing them generates false-positive risk flags on capabilities that simply have not been catalogued yet.

**Risk scores use heuristic weights, not validated predictors.** The formula combines severity, urgency, feasibility, conflict status, and ARR exposure into a transparent composite. The current weights and thresholds are product hypotheses intended for evaluation. They have not been statistically validated against churn, escalation, or revenue-loss outcomes. Rule-based overrides (critical legal issue, unsupported capability with committed date, overdue commitment without owner) take precedence over formula output for the highest-risk cases.

**Conflict detection is hybrid, not deterministic.** Date-infeasibility and capability-gap conflicts are detected deterministically. Cross-customer and self-contradiction conflicts use AI-assisted analysis. LLM-detected conflicts are surfaced as conflict candidates for human review, not confirmed facts.

---

## Research and Evaluation Context

PromiseGuard was developed as an AI Product Management portfolio project using secondary research, structured persona simulations, and controlled feasibility testing with synthetic sales-transcript data.

The extraction taxonomy, risk weights, thresholds, and workflow assumptions are product hypotheses. The four-class extraction system and possibility-language handling were informed by a manually constructed synthetic evaluation — a small, controlled feasibility test that demonstrates a failure pattern and product-design response; it does not represent production extraction accuracy or statistically validated performance.

The project has not been validated with production customers, live enterprise sales teams, or confirmed design partners. It demonstrates product framing, candidate-extraction design, human-review workflows, capability matching, risk-model experimentation, and full-stack execution as a portfolio proof of concept.

---

## Data Handling and Security

PromiseGuard handles sales calls, emails, and contracts that may contain confidential commercial terms, customer security details, and personally identifiable information.

The current implementation includes tenant-scoped data access, authenticated ingestion via Clerk, source-level provenance, and auditable review actions.

Planned enterprise-hardening areas:
- Webhook-signature verification for integration sources
- Encryption in transit and at rest for stored transcripts and contracts
- Configurable source retention and deletion policies
- Role-based access to legal and commercial commitment views
- PII and sensitive-data redaction before storage
- Immutable review and status-change history
- Tenant-isolation testing

---

## Portfolio Context

PromiseGuard is the third project in an AI operations portfolio covering the full agent and customer lifecycle.

| | PolicyLens AI | ExceptionLoop | PromiseGuard |
|--|--------------|---------------|--------------|
| **When** | Before deployment | After deployment | Sales to delivery |
| **What** | Tests agents against policy | Manages escalations + learns from them | Tracks every customer promise |
| **Output** | Launch-readiness report | Automation pipeline | Risk-scored commitment ledger |
| **North Star** | % critical policy rules tested before prod | % recurring exceptions converted to automation | % confirmed commitments with accepted owner, due date, source evidence, and capability status before delivery kickoff |

Extraction quality is tracked separately: candidate precision, possibility false-positive rate, reviewer confirmation rate, and percentage of high-risk commitments resolved before due date.

---

## About

PromiseGuard is a deployed, production-oriented portfolio MVP demonstrating:

- Four-class LLM candidate extraction with controlled evaluation of possibility-language handling
- Human review gate enforced at the data layer with full audit history including dismissed candidates
- Database-layer workflow constraints for legal-sensitive commitment categories
- pgvector semantic capability matching with four-state output
- Hybrid conflict detection combining deterministic and AI-assisted analysis
- Heuristic risk scoring with transparent component scores and rule-based overrides
- Integration-ready ingestion adapters for Gong, Salesforce, and Slack
- Authenticated full-stack deployment with Clerk v5 and tenant-scoped data access

**Built by [Rajender Gugulothu](https://github.com/rajendergugulothu)**

---

<div align="center">
  <em>PromiseGuard — Every promise tracked. Every risk surfaced.</em>
</div>
