# Frontier challenge agent team

These are role prompts for a small, evidence-first agent workflow. Use the
roles in order and save each agent's transcript under `trajectories/` using the
same role name. The human participant remains the decision maker for scope,
claims, and any consequential action.

## Recommended run order

1. `01-problem-scout.md` — select a narrow, safe use case and define success.
2. `02-workflow-architect.md` — turn it into a baseline, final workflow, and
   evaluation plan before implementation.
3. `03-builder.md` — implement one small, reproducible increment at a time.
4. `04-evaluator.md` — execute the fixed evaluation suite and report results.
5. `05-verifier.md` — independently check evidence, safety, and reproducibility.
6. `06-submission-editor.md` — prepare the README, changelog, reproduction
   guide, and video outline from verified facts only.

Do not run agents in parallel against the same files. Commit or snapshot each
accepted change, and record rejected experiments as well as successful ones.

## Shared operating rules

- Use public, synthetic, or explicitly approved data only; never place secrets
  in the repository or traces.
- Keep external and consequential actions simulated or behind explicit human
  approval. Do not make hiring, legal, medical, financial, or other high-impact
  decisions automatically.
- Preserve a fair comparison: baseline and final workflow receive the same
  inputs, cases, and scoring method. Document material resource differences.
- Make every factual claim traceable to a command, a fixture, a test, or a
  reviewed source. Label assumptions and uncertainty.
- Before editing, inspect the existing repository and state the files you plan
  to change. Run relevant checks after each change.

## Trajectory minimum

For each role, save the initial prompt, inputs, tool calls and outputs, retry or
failure details, human checkpoints, and final handoff. Redact keys, personal
data, and unnecessary local paths.
