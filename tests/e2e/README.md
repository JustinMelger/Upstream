# E2E Visual Regression

This folder contains browser smoke coverage and baseline images for visual checks.

CI currently runs the smoke flow with visual assertions enabled but strict baseline enforcement disabled. That means:
- current screenshots are still captured as artifacts
- missing or size-mismatched baselines do not fail CI yet
- non-strict visual issues are written as note artifacts in the screenshot directory
- intentional strict baseline enforcement remains deferred until the major UI surfaces settle

## Baseline workflow

1. Start API + UI locally (same as the e2e smoke target).
2. Create or refresh baselines:
   - `E2E_UPDATE_VISUAL_BASELINES=1 just e2e`
3. Review updated files in `tests/e2e/baselines/`.
4. Run strict checks:
   - `E2E_VISUAL_STRICT=1 just e2e`

## Environment contract

- Backend and UI must be reachable at `E2E_API_URL` and `E2E_UI_URL`.
- The smoke test expects a bootstrap admin user at `admin/admin`.
- The backend must allow the smoke flow to create one course and one path for the run.
- Visual captures use a fixed viewport and reduced-motion browser context to reduce incidental diffs.

## Environment flags

- `E2E_VISUAL_ASSERT` (default `1`): enable/disable visual assertions.
- `E2E_VISUAL_STRICT` (default `0`): fail if baseline is missing/size-mismatched.
- `E2E_UPDATE_VISUAL_BASELINES` (default `0`): write current screenshots as new baselines.
- `E2E_VISUAL_MAX_DIFF_PIXELS` (default `300`): allowed pixel delta before failure.
