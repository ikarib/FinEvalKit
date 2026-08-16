# Judge calibration, slices, drift, and observability

## Automated-judge calibration

`calibrate_judge` compares automated labels with independent human-gold labels. It reports a confusion matrix, accuracy, macro-F1, per-label precision/recall/F1, and Cohen's kappa. Cases enter manual review when labels disagree, confidence is below 0.80, or a high-risk answer receives a passing label.

The included 12-case dataset is an executable example, not evidence that a particular LLM judge is validated. Real use requires a larger, representative, independently labelled holdout and versioned judge model and prompt identifiers.

## Slice monitoring

`slice_report` calculates sample count, mean quality, pass rate, and a bootstrap interval for a chosen field such as modality or workflow. `max_mean_gap` is a triage signal. It must not be interpreted as proof of fairness or discrimination without relevant population, harm, and uncertainty analysis.

## Drift

`categorical_psi` compares baseline and current categorical distributions using population stability index (PSI):

- below 0.10: stable
- 0.10 to below 0.25: review
- 0.25 or above: material shift

These are configurable operating heuristics, not universal statistical guarantees.

## Experiment lineage

`JsonlTracker` records dataset, model, prompt, and code versions with each event. `WandbTracker` provides an optional adapter boundary. This gives every reported metric enough lineage for replay and comparison while keeping the default demo offline.
