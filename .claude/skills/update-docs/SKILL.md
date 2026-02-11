# Update Docs

Update project documentation to reflect recent code changes or newly implemented features.

## When to run

Run this skill after implementing new features, adding tools, changing architecture, modifying routes, or making any significant code changes.

## Steps

1. **Identify what changed.** Read the recent git diff against the main branch (`git diff main...HEAD` or `git diff HEAD~1`) to understand what was added, modified, or removed.

2. **Read all docs files.** Read every file in `docs/` and the root `README.md`:
   - `docs/FEATURES.md` — Implemented features table and recommended features table
   - `docs/ARCHITECTURE.md` — Infrastructure diagram, data flow, tool table, component table
   - `docs/DEPLOYMENT.md` — Deployment instructions
   - `docs/STANDARDS.md` — Coding standards and conventions
   - `docs/README.md` — Docs index
   - `README.md` — Root project README

3. **Update each relevant file.** For each change identified in step 1, update the appropriate docs:

   - **New feature or tool:** Add a row to the Implemented table in `docs/FEATURES.md` with the next sequential number, feature name, description, and current month/year. If the feature was in the Recommended table, update its Status to "Done" and add the date.
   - **New tool (function-calling):** Add a row to the Function-Calling Tools table in `docs/ARCHITECTURE.md` with tool name, direction, and purpose.
   - **New backend module:** Add a row to the Backend Components table in `docs/ARCHITECTURE.md`.
   - **New route:** Add a row to the WebSocket Routes or relevant route table in `docs/ARCHITECTURE.md`.
   - **Architecture changes:** Update the mermaid diagrams in `docs/ARCHITECTURE.md` if the data flow or infrastructure changed.
   - **New environment variables:** Add them to the relevant docs and `README.md`.
   - **Deployment changes:** Update `docs/DEPLOYMENT.md`.
   - **README-visible changes:** Update `README.md` if the change affects setup, features list, configuration, or usage instructions.

4. **Do not over-update.** Only modify docs that are actually affected by the code changes. Do not rewrite sections that are already accurate.

5. **Summarize.** After making all updates, provide a brief summary of which docs were updated and what was changed in each.
