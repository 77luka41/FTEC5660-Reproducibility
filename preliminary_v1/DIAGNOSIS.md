# Preliminary v1: retained real Colab logs

Source: user-provided repro_diagnostics.zip, received 14 November 2026. Original metadata/configuration and all uploaded logs are retained. This is an interrupted pilot, not the completed v2 comparison.

- Saved rows: baseline t0/i900 hit BudgetExceeded after 278 API attempts and 200,345 reported tokens; modified t0/i900 and t0/i901 completed without a valid final answer.
- Baseline t0/i901 was interrupted: 230 logged responses, no saved task result. It has no assigned success score or complete latency.
- Across all four trace logs: 748 successful responses, 494,099 reported tokens, no logged transient retries. This includes the interrupted instance, so it exceeds resources summed from the three saved rows. Unreturned requests can have unmeasured usage.
- Of 718 value responses, only 139 end with an exact label accepted by the original parser (19.36%).
- Thirty proposal responses contain 1,563 newline-separated lines, including 331 blanks. Upstream get_proposals treats every line as a candidate, including prose/Markdown. Traces retain blank or Markdown-only states.

The v1 adapter did not enforce the model-output interface. This observed failure motivates a separate v2 policy experiment. Both v2 widths are one with identical lower budgets; only the phase-specific system-message policy differs. It bounds proposals and specifies labels/final format as a single intervention, whose components are not separately ablated. No raw output is repaired by Python.

These records are not pooled with v2, and no failed outcome is replaced by a selected successful retry. The separate three-call v2 format probe is not an accuracy benchmark.
