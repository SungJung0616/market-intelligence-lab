# Analysis

This package interprets completed deterministic intelligence results. It may produce explanations,
risks, conflicting signals, and confidence notes, but it must never own, recalculate, or override
the underlying scores.

`inflation_explanation.py` provides the first rule-based explanation contract. It consumes an
`InflationResult` and exposes a concise interpretation, weighted contributions, strongest and
weakest evidence, conflicts, limitations, and confidence. It contains no AI calls, predictions,
recommendations, or score calculations.

`labor_explanation.py` consumes a completed `LaborResult` and identifies strongest and weakest
evidence, conflicting signals, risk flags, revision limitations, and confidence. Wage Pressure is
explained as a separate dimension and the explanation never recalculates Labor Health.

Owns explainable AI interpretation, supporting and conflicting evidence, risk summaries,
historical comparisons, and confidence estimates.

AI output must interpret and explain results produced by `market_intelligence_lab.intelligence`. This package
must not calculate, modify, or own the underlying deterministic market scores, and it must not
make investment decisions.
