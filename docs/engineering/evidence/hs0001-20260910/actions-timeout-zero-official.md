# GitHub Actions timeout-minutes: 0 official adjudication

Request type: Comprehensive research.

Version/date context: Retrieved 2026-09-10 KST. GitHub Docs are living docs. Runner source links are pinned to `actions/runner` commit `0e345bcaa292fea27a2f218c0edab3d3b93e1060` from `main` at retrieval time.

## Direct Answer

- Step-level `jobs.<job_id>.steps[*].timeout-minutes: 0` is unsupported by GitHub Docs. The workflow syntax docs say step `timeout-minutes` "must be a positive integer"; `0` is not positive.
- The statement "GitHub rejects the workflow before running it" is a supported inference from the workflow syntax requirement, not something the pinned open runner source proves by itself.
- Pinned runner schemas/source do not encode a minimum value for step timeout. They type it as `number`, convert it to `Int32`, and foreground/background step execution only calls `SetTimeout(...)` when the evaluated value is `> 0`. If `0` somehow reaches the worker, pinned runner source would treat it as no step timeout, not as an immediate timeout.
- Job-level `jobs.<job_id>.timeout-minutes` is different. The current docs describe it as the maximum minutes before GitHub automatically cancels the job and default it to `360`, but the job section does not state the same "positive integer" sentence that the step section does.
- Pinned runner parser/source also does not enforce `job timeout-minutes > 0`; it types job timeout as a number and converts it to `Int32`. Job timeout execution/cancellation is not proven from the worker source path inspected here, so job `0` acceptance/rejection should not be inferred from step docs.

## Official Docs Evidence

- GitHub Docs: Workflow syntax, `jobs.<job_id>.steps[*].timeout-minutes`
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsstep_idtimeout-minutes
  - Establishes step timeout semantics: maximum minutes before killing the step process; maximum `360`; fractional values are unsupported; `timeout-minutes` must be a positive integer.
  - Supported conclusion: `0` is invalid for step timeout because it is not a positive integer.

- GitHub Docs: Workflow syntax, `jobs.<job_id>.timeout-minutes`
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idtimeout-minutes
  - Establishes job timeout semantics: maximum minutes before GitHub automatically cancels the job; default `360`; runner execution limits may cancel earlier.
  - Boundary: this docs section does not state the step section's "positive integer" requirement.

## Source-Reference Evidence

Docs establish the user-facing support boundary. Runner source is used only to check whether the pinned open runner schema/source independently proves zero rejection.

- `actions/runner`: WorkflowParser schema, job timeout
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Sdk/WorkflowParser/workflow-v1.0.json#L1994-L1998
  - Establishes job `timeout-minutes` is typed as `number-strategy-context`.
  - Boundary: no minimum or positive constraint is visible in this schema entry.

- `actions/runner`: WorkflowParser schema, step timeout
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Sdk/WorkflowParser/workflow-v1.0.json#L2393-L2420
  - Establishes run/uses step `timeout-minutes` uses `step-timeout-minutes`.
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Sdk/WorkflowParser/workflow-v1.0.json#L2547-L2564
  - Establishes `step-timeout-minutes` is a `number`.
  - Boundary: no minimum or positive constraint is visible in this schema entry.

- `actions/runner`: WorkflowTemplateConverter, job/step timeout conversion
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Sdk/WorkflowParser/Conversion/WorkflowTemplateConverter.cs#L558-L570
  - Job timeout conversion asserts number and casts to `Int32`; no `> 0` validation is visible.
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Sdk/WorkflowParser/Conversion/WorkflowTemplateConverter.cs#L841-L853
  - Step timeout conversion asserts number and casts to `Int32`; no `> 0` validation is visible.

- `actions/runner`: WorkflowTemplateEvaluator, defaulting
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Sdk/WorkflowParser/WorkflowTemplateEvaluator.cs#L458-L485
  - Job timeout defaults to `360` only when unset/null; a provided numeric `0` would not be replaced by the default in this code.
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Sdk/WorkflowParser/WorkflowTemplateEvaluator.cs#L682-L706
  - Step timeout defaults to `0` when unset/null.

- `actions/runner`: StepsRunner foreground step timeout application
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Runner.Worker/StepsRunner.cs#L296-L313
  - Establishes worker evaluates step timeout and only calls `SetTimeout(TimeSpan.FromMinutes(timeoutMinutes))` when `timeoutMinutes > 0`.

- `actions/runner`: BackgroundStepCoordinator timeout application
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Runner.Worker/BackgroundStepCoordinator.cs#L213-L226
  - Establishes background step execution also only applies timeout when `timeoutMinutes > 0`.

## Supported vs Inference

- Supported by official docs: step `timeout-minutes: 0` is invalid/unsupported because step timeout must be a positive integer.
- Supported by pinned runner schema/source: runner schema/converter does not itself reject step `0`; worker execution would not set a timeout for `0`.
- Inference: GitHub rejects a workflow containing step `timeout-minutes: 0` before running it, because it violates the public workflow syntax. The exact rejecting service component/error path is not proven by the pinned open runner source inspected here.
- Supported by official docs: job timeout has documented default/cancellation semantics, but the current job section does not state the explicit step-only positive-integer sentence.
- Supported by pinned runner parser/source: job `timeout-minutes` is a number and conversion/defaulting does not show a `> 0` check.
- Not proven here: exact GitHub service behavior for `jobs.<job_id>.timeout-minutes: 0`. Do not carry the step positive-integer rule over to job timeout without a job-specific primary source.

## Reusable Takeaway

For V1 F-E, the strongest primary-source wording is: "Step `timeout-minutes: 0` is invalid by GitHub's workflow syntax docs; pinned runner source does not prove the rejection and would treat a reached value of `0` as no applied step timeout. Job timeout must be adjudicated separately; the cited job docs/source do not prove the same zero rejection."
