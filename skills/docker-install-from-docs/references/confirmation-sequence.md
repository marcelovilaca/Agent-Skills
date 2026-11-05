# Confirmation-sequence (this user)

This user's workflow from the session: structured task labels (C / B / A), confirmation gate before each step, README/development paper updated after each change, and step-by-step preference.

Rules:
- When user gives a labeled sequence (e.g. "C then B then A"), follow it in order; do not skip B (env/config) to start A (containers).
- Confirm B explicitly (show grep of changed .env lines) before A.
- Write README.md at folder creation, not at end; update it if any file changes.
- If user says "done changing the password", treat as B-confirmed; then ask if any other B adjustments needed before A.
- Confirmation gate applies to new dev tasks (per user profile: "confirmation gate required before every new dev task").
