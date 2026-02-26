# E2E Visual Regression

This folder contains browser smoke coverage and baseline images for visual checks.

## Baseline workflow

1. Start API + UI locally (same as the e2e smoke target).
2. Create or refresh baselines:
   - `E2E_UPDATE_VISUAL_BASELINES=1 just e2e`
3. Review updated files in `tests/e2e/baselines/`.
4. Run strict checks:
   - `E2E_VISUAL_STRICT=1 just e2e`

## Environment flags

- `E2E_VISUAL_ASSERT` (default `1`): enable/disable visual assertions.
- `E2E_VISUAL_STRICT` (default `0`): fail if baseline is missing/size-mismatched.
- `E2E_UPDATE_VISUAL_BASELINES` (default `0`): write current screenshots as new baselines.
- `E2E_VISUAL_MAX_DIFF_PIXELS` (default `300`): allowed pixel delta before failure.
