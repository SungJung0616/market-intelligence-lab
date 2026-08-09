# AGENTS.md

## Purpose

This document defines how AI agents implement changes in Market Intelligence Lab. Notion is the source of truth for the project's Goal, Vision, Roadmap, and Architecture.

## Development Principles

- Prefer simple, correct, and maintainable solutions.
- Make the smallest change that satisfies the requirement.
- Follow existing patterns and avoid unrelated refactoring.
- Do not add speculative features or premature abstractions.
- State important assumptions, risks, or uncertainty.
- Never commit secrets, private data, or proprietary datasets.

## General Rules

- If information is missing, do not guess.
- Read the relevant files before making assumptions.
- Ask for clarification when requirements are ambiguous.
- Do not optimize code that has not been measured.
- Do not rewrite working code without a clear reason.

## Project Workflow

Before changing code:

1. Read this file and relevant Notion documentation.
2. Inspect the existing code, tests, and repository state.
3. Confirm the task fits the documented architecture.
4. Identify the smallest complete implementation.

During implementation:

- Keep changes focused and reversible.
- Preserve unrelated work.
- Validate changes as you proceed.
- Ask for clarification when requirements materially affect the solution.

## Coding Standards

- Follow the repository's configured language and framework conventions.
- Use clear names, small cohesive modules, and explicit interfaces.
- Separate business logic from infrastructure and presentation concerns.
- Validate inputs and handle expected failures.
- Avoid duplicated logic and unnecessary dependencies.
- Do not suppress lint, type, security, or test failures without explanation.
- Write comments only when they clarify intent or constraints.

## Architecture Approval

Do not change documented architecture, public interfaces, data schemas, security boundaries, financial calculations, or core technology choices without approval.

For a necessary architectural change:

1. Explain the problem and proposed solution.
2. Describe important tradeoffs and migration impact.
3. Wait for explicit human approval.
4. Record the approved decision in Notion or an Architecture Decision Record.

## Testing Expectations

- Add or update tests for every behavior change.
- Include regression tests for bug fixes when practical.
- Test important success, boundary, and failure cases.
- Use deterministic fixtures for financial calculations.
- Isolate external services in unit tests.
- Run relevant formatting, linting, type-checking, test, and build commands.
- Never weaken or remove tests merely to make a change pass.
- Report any checks that could not be run.

## Documentation Rules

- Update documentation when behavior, setup, configuration, or interfaces change.
- Document new environment variables in `.env.example` without real secrets.
- Keep implementation documentation in the repository.
- Keep Goal, Vision, Roadmap, and Architecture in Notion.
- Record significant architectural decisions in the agreed source of truth.

## Definition of Done

Work is complete when:

- The approved requirement is implemented.
- The change follows the documented architecture and repository conventions.
- Relevant tests and checks pass.
- Error handling and security implications have been considered.
- Documentation is current.
- No secrets, debug artifacts, or unrelated changes are included.
- Assumptions, limitations, and unverified checks are reported.

## Agent Boundaries

Do not deploy, merge, modify production data, execute trades, or perform irreversible external actions without explicit human approval.
