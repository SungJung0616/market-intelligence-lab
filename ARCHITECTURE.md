# Market Intelligence Lab Architecture

Notion is the source of truth for architectural decisions. This document maps the approved
Market Intelligence Lab Version 0.1 architecture to repository boundaries.

## System Flow

```text
Data Sources
    ↓
Collection
    ↓
Storage
    ↓
Market Intelligence
    ↓
AI Analysis
    ↓
Presentation
```

Scheduled jobs coordinate this flow without owning its business logic.

## Repository Boundaries

| Package | Responsibility |
|---|---|
| `market_intelligence_lab.collection` | Retrieve, validate, normalize, and deduplicate external data |
| `market_intelligence_lab.storage` | Persist approved structured and flexible data |
| `market_intelligence_lab.intelligence` | Calculate deterministic market intelligence |
| `market_intelligence_lab.analysis` | Explain evidence, risks, comparisons, and confidence |
| `market_intelligence_lab.presentation` | Present research through human-facing interfaces |
| `market_intelligence_lab.jobs` | Orchestrate scheduled workflows |

Dependencies should flow from orchestration toward explicit interfaces. Data-provider,
persistence, intelligence, AI, and presentation concerns must remain separable and testable.

`market_intelligence_lab.intelligence` exclusively owns deterministic market calculations and
scoring. `market_intelligence_lab.analysis` consumes those results to produce AI-assisted explanations, risks,
conflicting-signal summaries, historical context, and confidence notes. Analysis must never own
or alter the underlying score calculations.

## Product and Model Evolution

The primary presentation remains simple and stable: current score and regime, historical
baseline, change, major contributors, relevant events, and confidence. Detailed evidence is
progressively disclosed rather than placed on the primary view.

The intelligence model is expected to evolve as research improves its data, baselines,
normalization, weights, event treatment, and confidence rules. Each material model change must:

- have an explicit version and documented rationale;
- reproduce a result from defined data and rules;
- be compared against the previous version on fixed historical cases;
- preserve the model version used for previously generated results; and
- keep AI interpretation separate from deterministic score calculation.

## Testing Boundaries

- `tests/unit/` isolates external systems and validates deterministic behavior.
- `tests/integration/` validates controlled system boundaries.
- `tests/fixtures/` contains small, deterministic, non-proprietary inputs.

## Data Boundaries

`data/raw/` and `data/processed/` are local working directories. Their generated contents are
excluded from Git. PostgreSQL remains the approved primary database, with JSONB available for
flexible raw responses and AI analysis output.

## Change Control

Changes to these boundaries, data schemas, scoring methodology, security controls, public
interfaces, or core technologies require explicit approval and an updated Notion decision.
