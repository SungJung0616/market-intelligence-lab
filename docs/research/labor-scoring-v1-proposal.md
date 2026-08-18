# Labor Intelligence v1 — Scoring Curve Proposal

Status: **Approved and implemented as Labor Intelligence v1.0 on 2026-08-14**
Evidence version: `labor-distribution-v1`
Data reviewed through: 2026-08-01

## Responsibility

Labor Health measures labor-market health and resilience. It does not infer Risk-On/Off,
stock-market direction, recession certainty, or an investment recommendation. Wage Pressure is a
separate signal.

All curves below use continuous linear interpolation between anchors and clamp outside the stated
range. Recent five-year percentile remains explanation-only in v1 because pandemic observations
materially distort several distributions.

## Proposed Top-Level Weights

| Component | Weight |
|---|---:|
| Payroll Momentum | 30% |
| Unemployment Health | 30% |
| Initial Claims | 25% |
| JOLTS Demand | 15% |

These are approved v1 weights. They are deterministic research rules, not validated predictive
weights, and remain subject to documented future revision.

## 1. Payroll Momentum

Internal formula: 75% three-month average payroll gain + 25% acceleration (`3M average - 6M
average`). The monthly change is displayed but not separately weighted because the three-month
average already contains it.

### Three-month average anchors

| Monthly jobs (thousands) | 3M level score | Interpretation |
|---:|---:|---|
| -100 | 0 | Clear contraction |
| 0 | 20 | Stalling |
| 50 | 40 | Weak |
| 100 | 55 | Moderate |
| 175 | 75 | Healthy |
| 250 | 90 | Very strong |
| 350 | 100 | Exceptional |

### Acceleration anchors

| 3M minus 6M (thousands) | Trend score |
|---:|---:|
| -100 | 0 |
| -50 | 25 |
| -25 | 40 |
| 0 | 60 |
| 25 | 75 |
| 50 | 90 |
| 100 | 100 |

Proposed flags: `PAYROLL_CONTRACTION` when the 3M average is below zero;
`PAYROLL_DECELERATION` when the 3M average is below 50K and acceleration is below -25K.

## 2. Unemployment Health

Internal formula: 55% current unemployment-rate health + 45% Sahm-type deterioration score. The
3M and 6M changes remain supporting evidence to prevent a single derived signal from hiding the
path.

### Current-rate anchors

| Unemployment rate | Health score |
|---:|---:|
| 3.0% | 100 |
| 3.5% | 95 |
| 4.0% | 85 |
| 4.5% | 70 |
| 5.0% | 50 |
| 6.0% | 25 |
| 8.0% | 0 |

### Sahm-type gap anchors

The gap is the current 3M unemployment-rate average minus the lowest 3M average in the previous
12 months.

| Gap | Deterioration score |
|---:|---:|
| 0.00 pp | 100 |
| 0.10 pp | 85 |
| 0.20 pp | 70 |
| 0.30 pp | 50 |
| 0.40 pp | 25 |
| 0.50 pp | 0 |

Proposed flags: `UNEMPLOYMENT_DETERIORATION_WATCH` at 0.30 pp and
`SAHM_THRESHOLD_REACHED` at 0.50 pp. The latter is a warning signal, not a recession declaration.

## 3. Initial Claims

Internal formula: 50% current 4W average + 50% 13W percentage change. Weekly data remain weekly.

### Four-week-average anchors

| Claims | Level score |
|---:|---:|
| 175K | 100 |
| 200K | 90 |
| 225K | 75 |
| 250K | 55 |
| 300K | 25 |
| 400K | 0 |

### Thirteen-week-change anchors

| Change | Trend score |
|---:|---:|
| -15% | 100 |
| -5% | 85 |
| 0% | 65 |
| +5% | 45 |
| +10% | 25 |
| +15% | 10 |
| +25% | 0 |

Proposed flags: `CLAIMS_DETERIORATION_WATCH` at +10%; `CLAIMS_DETERIORATION` at +15%;
`CLAIMS_LEVEL_CONFIRMATION` when the 4W average is at least 250K. The fixed level curve should be
revisited if long-run labor-force scaling proves material.

## 4. JOLTS Demand

Internal formula: 75% openings per unemployed worker + 25% three-month ratio change. Openings level
and openings rate remain visible context but are not weighted.

### Openings-per-unemployed anchors

| Ratio | Demand score | Interpretation |
|---:|---:|---|
| 0.4 | 0 | Severe demand weakness |
| 0.6 | 25 | Weak |
| 0.8 | 50 | Soft |
| 1.0 | 70 | Broad balance |
| 1.2 | 85 | Strong |
| 1.5 | 95 | Very strong / overheating watch |
| 2.0 | 100 | Extreme demand / overheating |

### Three-month-change anchors

| Ratio change | Trend score |
|---:|---:|
| -0.30 | 0 |
| -0.15 | 25 |
| -0.05 | 45 |
| 0.00 | 60 |
| +0.05 | 75 |
| +0.15 | 95 |
| +0.30 | 100 |

Proposed flags: `LABOR_DEMAND_WEAK` below 0.8; `LABOR_DEMAND_SEVERE` below 0.6;
`LABOR_DEMAND_OVERHEATING` at or above 1.5. Overheating can coexist with a high Labor Health
component score.

## Separate Wage Pressure Signal

Proposed formula: 70% AHE YoY + 30% AHE 3M annualized. Higher means more wage pressure, not better
labor health.

| Wage growth | Pressure score |
|---:|---:|
| 2.0% | 10 |
| 2.5% | 25 |
| 3.0% | 40 |
| 3.5% | 55 |
| 4.0% | 70 |
| 5.0% | 90 |
| 6.0% | 100 |

Trend uses `3M annualized - YoY`: Cooling below -0.30 pp, Stable from -0.30 to +0.30 pp, and
Reaccelerating above +0.30 pp. Negative wage growth raises a separate downside-risk flag rather
than being presented as desirable low pressure.

## Representative Scenario Checks

- Payroll +150K 3M average with no acceleration: approximately 66 — healthy but not exceptional.
- Unemployment 4.5% with a 0.30 pp Sahm-type gap: approximately 61 — still moderate, visibly
  deteriorating.
- Claims 225K with a +15% 13W change: approximately 43 — acceptable level with a serious early
  warning.
- JOLTS ratio 1.0 with no 3M change: approximately 68 — broadly balanced.
- JOLTS ratio 1.6: high health score plus an overheating flag; the flag is not hidden by the score.

## Approval Questions

1. Approve or revise each component's internal weights.
2. Approve or revise the anchor tables and flag thresholds.
3. Decide whether the Claims level should later be normalized by covered employment.
4. Confirm Recent 5Y Position remains explanation-only in v1.
5. Approve representative scenario behavior before production implementation.
