# Intelligence

This package owns deterministic market calculations and scoring. AI interpretation belongs in
`analysis` and must not recalculate or override these results.

## Inflation Score v1

`inflation.py` combines Core PCE (35%), Core CPI (30%), Headline PCE (20%), and Headline CPI
(15%). Each indicator is evaluated through Current Pressure (50%), Trend (30%), and Recent 5Y
Position (20%).

Higher scores mean **lower inflation pressure**. `Cooling` therefore produces a higher score;
`Reaccelerating` produces a lower score. This is not a Risk-On/Off or investment signal.

The calculation requires all four series and 64 contiguous monthly observations. Missing months
normally make the combined result unavailable, and weights are never silently renormalized.

One explicit structural-gap exception exists: October 2025 CPI and Core CPI were not published
because of the federal funding lapse. Version 1.1 estimates that month during calculation using the
geometric mean of the adjacent September and November index levels, matching the approach BLS
documented for seasonal-adjustment continuity. Raw FRED artifacts are never modified. Results expose
the imputed date and a data-quality note. Any other missing month remains an error.

Version 1.1 uses latest revised FRED data and is not vintage-safe.

## Labor Intelligence v1

`labor_distribution.py` transforms seven official FRED dependencies into descriptive candidate
metrics. `labor.py` alone owns the approved Labor Health calculation: Payroll Momentum (30%),
Unemployment Health (30%), Initial Claims (25%), and JOLTS Demand (15%). Higher means healthier
and more resilient labor conditions.

Wage Pressure is calculated and reported separately; it never contributes to Labor Health. Recent
5Y percentiles are explanatory context only. Labor Intelligence does not infer Risk-On/Off,
recession certainty, stock direction, or an investment recommendation. Version 1.0 uses latest
revised FRED data and is not vintage-safe.

Owns deterministic market direction, sector rotation, macro, breadth, money-flow, sentiment,
event-risk calculations, and market scoring.

Every score must be reproducible from defined inputs and rules. This package must not perform
data retrieval, AI interpretation, or presentation. It is the sole owner of underlying score
calculations.
