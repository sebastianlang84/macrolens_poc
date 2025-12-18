# Design: Robust Analysis & Synthesis ("Best-of")

## 1. Problem Statement

Current LLM-based market analyses suffer from common "Generative AI" weaknesses:
1.  **Hallucinated Math:** LLMs often miscalculate spreads (e.g., 10Y-2Y yield curve) or percentage changes.
2.  **Blindness to Outliers:** Without statistical context, an LLM might miss a 3-sigma move in Gold or treat a data error as a real trend.
3.  **False Confidence:** LLMs rarely admit when data is missing or stale, leading to "plausible but wrong" advice.
4.  **Model Bias:** OpenAI models tend to be conservative/hedging, while Gemini models can be more creative but prone to speculation.

## 2. Solution Overview: "Code-First, LLM-Second"

To solve this, we shift the burden of **calculation** and **fact-checking** from the LLM to deterministic Python code. The LLM's role shifts from "Calculator" to "Interpreter".

We also introduce a **Synthesis Layer** that combines diverse model perspectives into a single, robust report.

## 3. Component 1: Computed Metrics (The "Fact Sheet")

Instead of asking the LLM to "calculate the yield curve spread", we compute it in `ReportV1` and pass it as a first-class citizen in the JSON payload.

### 3.1 New `ComputedSeries` Concept
We will introduce a mechanism to define derived series in `ReportV1`.

**Examples:**
*   **Yield Curve:** `US10Y - US2Y`
*   **Real Rates:** `US10Y - CPI (YoY)`
*   **Credit Spreads:** `High Yield - Treasury`

### 3.2 Implementation Strategy
*   Extend `ReportV1` dataclass to include a `computed_metrics` dictionary.
*   During `generate_report_v1`, calculate these values using pandas.
*   **Crucial:** If inputs are missing/stale, the computed metric must be explicitly marked as `null` or `stale`.

## 4. Component 2: Anomaly Detection (The "Sanity Check")

We need to statistically ground the LLM's qualitative assessment.

### 4.1 Z-Score Calculation
For every series, we calculate a Z-Score based on a rolling window (e.g., 1-year lookback).
$$ Z = \frac{Current - Mean_{1y}}{StdDev_{1y}} $$

### 4.2 "Anomaly" Flags
In the JSON passed to the LLM, we add an `anomaly_flag` field for each series:
*   `NORMAL`: -1.5 < Z < 1.5
*   `ELEVATED`: |Z| > 1.5
*   `EXTREME`: |Z| > 3.0

**Prompt Instruction:** "Pay special attention to any series marked 'EXTREME'. These are statistical outliers."

## 5. Component 3: Confidence & Staleness (The "Honesty Protocol")

We must force the LLM to acknowledge data quality issues.

### 5.1 Data Quality Context
The JSON payload will include explicit "Freshness" metadata for every data point:
```json
{
  "id": "gold",
  "last_value": 2050.5,
  "last_updated": "2025-12-10", // 5 days ago!
  "freshness": "STALE" // Computed by Python
}
```

### 5.2 Prompt Engineering
Update `system.md`:
> "You are a skeptical analyst.
> 1. Check the 'freshness' field. If data is STALE (>3 days old), you MUST qualify your analysis with 'Based on data from [Date]...'.
> 2. If a computed spread is missing, state 'Insufficient data to calculate spread' rather than guessing.
> 3. Provide a **Confidence Score (0-100%)** at the end of your summary, based on data completeness and market clarity."

## 6. Component 4: Synthesis Workflow ("Best-of")

We will implement a multi-step pipeline to get the best of both worlds (Conservative OpenAI + Creative Gemini).

### 6.1 The Workflow
1.  **Step 1: The Analyst (OpenAI GPT-4o)**
    *   Role: Conservative, fact-focused, risk-averse.
    *   Task: "Analyze the data. Focus on downside risks and discrepancies."
    *   Output: `analysis_conservative.md`

2.  **Step 2: The Contrarian (Google Gemini 2.0)**
    *   Role: Creative, pattern-seeking, forward-looking.
    *   Task: "Look for non-obvious correlations and upside scenarios. Challenge the consensus."
    *   Output: `analysis_creative.md`

3.  **Step 3: The Synthesizer (OpenAI GPT-4o or Strongest Model)**
    *   Input: `analysis_conservative.md`, `analysis_creative.md`, `Fact Sheet (JSON)`
    *   Task: "Merge these two perspectives.
        *   Where they agree, state it as high confidence.
        *   Where they disagree, check the 'Fact Sheet'.
        *   If one hallucinates (contradicts the Fact Sheet), discard that point.
        *   Create a balanced 'Best-of' report."
    *   Output: `final_report.md`

## 7. Implementation Roadmap

1.  **Phase 1: Hardening the Data (Python)**
    *   Implement `ComputedMetrics` in `ReportV1`.
    *   Implement `ZScore` calculation in `ReportV1`.
    *   Add `freshness` flags to JSON output.

2.  **Phase 2: Prompt Updates**
    *   Update `system.md` to enforce "Honesty Protocol".
    *   Update `user.md` to present the new "Fact Sheet" structure clearly.

3.  **Phase 3: Synthesis Pipeline**
    *   Create a new `SynthesisService` (or extend `AnalysisService`).
    *   Implement the 3-step workflow.

## 8. Example JSON Structure (Target)

```json
{
  "meta": { "as_of": "2025-12-15" },
  "computed_metrics": {
    "yield_curve_10y_2y": {
      "value": -0.45,
      "status": "INVERTED",
      "z_score": -1.2
    }
  },
  "series": [
    {
      "id": "gold",
      "value": 2100,
      "z_score": 3.1,
      "anomaly": "EXTREME",
      "freshness": "OK"
    },
    {
      "id": "bitcoin",
      "value": 98000,
      "freshness": "STALE (5 days)"
    }
  ]
}