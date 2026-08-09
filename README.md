# Market Intelligence Lab

> **We don't predict stocks. We decode the market.**

A testable, explainable market research platform focused on evidence—not stock prediction.

Market Intelligence Lab transforms complex financial data into objective scores, explainable insights, and actionable market intelligence. Its purpose is not to predict individual stocks or replace investment decisions. It helps investors understand the market environment before deciding where—and whether—to invest.

## Project Overview

Financial markets produce signals across indexes, interest rates, volatility, currencies, commodities, sectors, market breadth, capital flows, sentiment, macroeconomic data, and events.

These signals are related, but they are usually presented through separate tools and interpreted manually. Market Intelligence Lab brings them together into a measurable and explainable market intelligence system.

The platform is intended to answer questions such as:

- Is the market Risk-On, Neutral, or Risk-Off?
- Which sectors are gaining or losing strength?
- Where is capital flowing?
- Is market participation broad or concentrated?
- What is the market rewarding or avoiding?
- What is changing beneath the surface?
- Which evidence supports the conclusion?
- How confident should we be?

## Why This Project Exists

Understanding the market currently requires reviewing dozens of disconnected indicators, including:

- S&P 500, Nasdaq, Dow, and Russell 2000
- Treasury yields and macroeconomic indicators
- VIX, Dollar Index, oil, and gold
- Sector rotation and relative strength
- Market breadth and participation
- ETF, institutional, insider, and options flows
- News, earnings, and scheduled market events

Looking at these indicators independently can lead to conclusions shaped by narrative, recency, or emotion.

Market Intelligence Lab exists to replace that fragmented process with a repeatable research framework. It will measure market conditions, track how they change, and explain the evidence behind every conclusion.

A result should not end with:

> Today’s market score is 78.

It should explain:

> Today’s market score is 78 because Treasury yields are falling, capital is flowing into technology, market breadth is improving, and the VIX remains stable.

The score summarizes the market. The reasoning makes it useful.

## Vision

Use AI to replace assumptions with evidence.

Turn complex market data into clear and actionable insights. Understand the market through data rather than emotion, and continuously improve the quality of investment decisions through learning and validation.

## Product Principles

> **Simple on the surface. Rigorous underneath.**

The primary view should let a person understand the current market environment within seconds. It should lead with:

- Today's market score and regime
- Change versus the previous period and a defined historical baseline
- The strongest positive and negative contributors
- Relevant events and their measured impact
- Confidence, uncertainty, and conflicting signals

Detailed indicators and charts should remain available on demand without overwhelming the primary view. The interface should stay stable and intuitive while the intelligence model evolves through research.

Scoring is a living research model, not a fixed claim of truth. Data inputs, baselines, normalization rules, weights, event adjustments, and confidence methods may improve over time, but every change must remain explicit, versioned, reproducible, and historically validated.

## What Market Intelligence Lab Is Not

Market Intelligence Lab is not:

- A stock prediction engine
- A stock recommendation service
- An automated trading platform
- A replacement for investor judgment
- A guarantee of investment performance

AI should explain the market, identify evidence and risks, and communicate uncertainty. The final investment decision remains human.

## Current Project Status

Market Intelligence Lab is currently completing **Phase 1 — Project Foundation**.

Completed:

- Project Goal, Vision, and Roadmap defined
- Initial architecture documented
- Core technology decisions recorded
- Public Git repository established
- Development rules created for human and AI contributors
- Python 3.13 and uv development environment configured
- Application and test package structure created
- Linting, type-checking, and test tooling configured

Implemented in the first data vertical slice:

- FRED DGS10 collection with response validation
- Deterministic local JSON artifacts
- Unit tests isolated from the live provider
- Minimal Streamlit and Plotly data preview

Not yet implemented:

- Database schema
- Market scoring methodology
- Market intelligence engine
- AI analysis engine
- Research dashboard

The project foundation is complete. No market-data collection, scoring, or AI-analysis behavior has been implemented yet.

## Market Intelligence Framework

The initial system will study the market across the following dimensions:

| Dimension | Primary question |
|---|---|
| Market direction | Is the overall market strengthening or weakening? |
| Sector rotation | Where is relative and institutional strength developing? |
| Macro conditions | What economic conditions may be driving the market? |
| Market breadth | How widely is the market participating? |
| Money flow | Where is capital moving? |
| Sentiment | What is the market rewarding or fearing? |
| Event risk | Which events may affect current conditions? |

These dimensions will contribute to an explainable market regime:

- **Risk-On**
- **Neutral**
- **Risk-Off**

The scoring methodology, weights, and confidence rules are **To be defined** through research and historical validation.

## Technology Stack

Technology supports the research process; it does not define the project.

| Area | Current decision |
|---|---|
| Data collection and analysis | Python |
| Primary database | PostgreSQL |
| Flexible data storage | PostgreSQL JSONB |
| Initial dashboard | Streamlit |
| Visualization | Plotly or native Streamlit charts |
| AI model and provider | To be defined |
| Initial market data provider | FRED (DGS10) |
| Deployment platform | To be defined |

MongoDB is not planned for the initial version. It may be reconsidered if future requirements involve large volumes of unstructured news or document data.

A future version may use a Next.js or React frontend with a Python backend API.

## Planned System Flow

```text
Market, macro, SEC, news, and event data
                    ↓
            Python Data Collector
                    ↓
             PostgreSQL Database
                    ↓
        Market Intelligence Engine
                    ↓
             AI Analysis Engine
                    ↓
             Research Dashboard
                    ↓
           Scheduled Market Briefs
```

The AI analysis should:

- Generate and explain market scores
- Compare current conditions with historical environments
- Identify supporting and conflicting evidence
- Highlight market risks
- Estimate confidence
- Produce concise market summaries

## Development Environment

Market Intelligence Lab uses CPython 3.13 and [uv](https://docs.astral.sh/uv/) for Python version,
virtual environment, dependency, and lockfile management.

### Prerequisites

- Git
- uv

On Windows, install uv with the official installer:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart the terminal after installation, then prepare the project environment:

```powershell
git clone https://github.com/SungJung0616/market-intelligence-lab.git
cd market-intelligence-lab
uv python install 3.13
uv sync
```

Run all Python and development commands through uv:

```powershell
uv run python --version
uv run ruff check .
uv run mypy .
uv run pytest
```

Copy `.env.example` to `.env`, add your personal FRED API key, and collect the initial dataset:

```powershell
uv run --env-file .env python -m market_intelligence_lab.jobs.collect_dgs10
```

Launch the local data preview:

```powershell
uv run streamlit run src/market_intelligence_lab/presentation/app.py
```

The generated JSON is stored under `data/raw/fred/dgs10/` and remains excluded from Git.
This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank
of St. Louis.

The local `.venv` directory is managed by uv and must not be committed. Runtime
dependencies belong in `[project.dependencies]`; development-only tools belong in
`[dependency-groups].dev`. Commit `uv.lock` whenever dependencies change.

## Development Workflow

1. Read `AGENTS.md` and the relevant Notion decisions.
2. Start from an approved market question or implementation requirement.
3. Inspect the repository before making assumptions.
4. Implement the smallest complete change.
5. Validate calculations with deterministic data and historical cases.
6. Add or update relevant tests and documentation.
7. Run applicable formatting, linting, type-checking, testing, and build checks.
8. Request approval before changing architecture, schemas, scoring methodology, or core technologies.

Notion is the source of truth for the Goal, Vision, Roadmap, and Architecture. The repository documents their implementation.

## Roadmap Summary

### Phase 1 — Project Foundation

Establish the project structure, development environment, Git workflow, and basic data pipeline.

### Phase 2 — Market Intelligence

Collect and analyze market indexes, sector rotation, macroeconomic indicators, market breadth, capital flows, sentiment, and events.

### Phase 3 — AI Analysis

Explain market conditions, generate market scores, compare historical environments, identify risks, and communicate confidence.

### Phase 4 — Decision System

Combine validated market intelligence and explainable AI analysis into a structured decision-support system.

## Repository Structure

```text
market-intelligence-lab/
├── src/market_intelligence_lab/
│   ├── collection/    # External data retrieval and validation
│   ├── storage/       # PostgreSQL, JSONB, and artifact persistence
│   ├── intelligence/  # Deterministic market intelligence
│   ├── analysis/      # Explainable AI analysis
│   ├── presentation/  # Human-facing research views
│   └── jobs/          # Scheduled workflow orchestration
├── tests/
│   ├── unit/          # Isolated deterministic tests
│   ├── integration/   # Controlled boundary tests
│   └── fixtures/      # Small non-proprietary test inputs
├── data/
│   ├── raw/           # Local immutable source responses
│   └── processed/     # Local normalized and derived artifacts
├── AGENTS.md          # Rules for human and AI contributors
├── ARCHITECTURE.md    # Repository-level architecture mapping
└── README.md          # Project philosophy and development entry point
```

Generated data under `data/raw` and `data/processed` is excluded from Git. Each package README
defines its responsibility and prohibited concerns.

## Next Milestone

Define and validate the next market question using the proven data pipeline.

The milestone includes:

- Review the DGS10 preview and confirm the displayed baseline is useful.
- Select the next evidence dimension without introducing a composite market score yet.
- Define its provider, validation rules, historical baseline, and acceptance criteria in Notion.
- Extend the pipeline with isolated tests before connecting it to broader intelligence.

The immediate objective remains evidence quality, not investment signals or predictions.
