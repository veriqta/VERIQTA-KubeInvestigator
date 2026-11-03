# Provider configuration and evaluation

Evidence and interpretation are separate settings: `KI_SOURCE=fixture|kubernetes` and `KI_PROVIDER=mock|openai`. Fixture evidence requires mock. Mock interpretations are visibly labelled, require no provider key and make no model request. Real Kubernetes evidence can be collected with a mock provider; this validates collection and enforcement, not AI quality.

The live adapter uses OpenAI Chat Completions JSON mode, a fixed verified-TLS destination, no redirects, no automatic retries, a 20-second request timeout and a bounded streamed response. GPT-6 candidates use `reasoning_effort=none`. Structured tools and references are validated outside the model. Errors become honest failed reports rather than substituted mock diagnoses. Selected-field evidence is redacted before submission; residual confidential-data risk remains. Provider retention and billing are external responsibilities.

The current candidate is **gpt-6-luna**, configurable through `KI_MODEL`. No live model configuration or account access has been tested. The earlier GPT-4.1 mini candidate is deprecated, with its snapshot scheduled for removal on January 14, 2027 according to the [official deprecations](https://developers.openai.com/api/docs/deprecations). The [GPT-6 Luna page](https://developers.openai.com/api/docs/models/gpt-6-luna) documents Chat Completions and standard pricing; model availability must be rechecked before evaluation. ChatGPT subscriptions do not establish API access or credits.

## Proposed bounded live evaluation — not executed

The no-call plan is reproducible:

```sh
.venv-source/bin/python scripts/evaluate.py --plan
```

The suite contains **eight investigations**, including all three conditions, ambiguity, a healthy pod, a missing workload, an explicit scenario mismatch and an unsupported request. Each has expected evidence and acceptable uncertainty in [cases](../evals/cases.json). Prepare the disposable samples, including examples/evidence-cases.yaml, with optional logs enabled. Preserve their original failure state for evaluation; corrected browser samples are not suitable without a reset.

The proposed provider is OpenAI `gpt-6-luna`, standard processing with reasoning disabled. Limits are six model turns per investigation, **48 total requests at most**, eight Kubernetes tools per investigation, 90 seconds of running work, 48,000 payload characters and 1,600 output tokens per request. Calls are sequential and never automatically retried. Explicit mismatches can terminate without a provider request.

At the official rates checked November 2, 2026—$0.10 per million uncached input tokens and $0.50 per million output tokens—a conservative allowance of 50,000 input tokens plus 1,600 output tokens per request gives an estimated envelope of **$0.2784**. The proposed budget is **$0.50**. This is not a guaranteed bill or a hard provider-side cap: recheck pricing/account access, apply provider billing controls, and obtain separate authorisation before any paid execution. No cost or accuracy result has been observed.

## Authorisation and setup status

The recorded eight-investigation, maximum 48-request, proposed $0.50 evaluation remains **unauthorised** as of November 3, 2026. The candidate-workflow dispatch approval authorised artifact preparation only; it did not approve paid model calls. Approval requested for the existing bounded plan: OpenAI `gpt-6-luna`, eight investigations, at most 48 requests, the stated per-request/tool/time limits, no automatic retries, and the proposed $0.50 budget envelope. Authorisation has not been granted. The remaining decision is explicit approval of this exact evaluation scope and budget, not another candidate-workflow approval. No live calls have been made.

A presence-only local check found neither `KI_API_KEY` in the current process environment nor the designated `.data/live.env` file. It did not inspect secret values or search other credential stores, so it does not establish that no organisation credentials exist elsewhere. Before execution, an authorised operator must configure a restricted evaluation-project provider credential server-side and confirm access, current pricing and billing controls. Provider budget alerts may not enforce a hard $0.50 spending cap; the proposed envelope is not a billing guarantee.

## Secure execution prerequisites

Use only an authorised disposable deployment exposed through an explicit localhost port-forward. Keep a high-entropy team token and provider API key in a private server-side environment file or existing Kubernetes Secret containing `KI_TOKEN` and `KI_API_KEY`. For a local environment file, use a private directory and mode 0600 (with `umask 077`), a private editor or secret-manager injection, and an ignored path such as `.data/live.env`; do not type keys into shell command history. For Helm, create/update the Secret from that private file and reference `existingSecret`; restrict Secret-reader access and use cluster encryption at rest where available. Never put real values in source, Helm values, URLs, screenshots or chat. Configure `provider=openai`, `model=gpt-6-luna`, `logs=true` and only `veriqta-demo`; use the documented [installation Secret procedure](installation.md). No key is delivered to the browser or evaluation output. A Secret's base64 representation is not encryption.

After independent paid-call authorisation and private configuration, the explicit execution command is:

```sh
# KI_TOKEN is the team token, not the provider key. Configure it privately.
.venv-source/bin/python scripts/evaluate.py --run --acknowledge-paid-calls \
  --url http://127.0.0.1:18080 --output .data/live-evaluation-NEW-RUN.json
```

The harness refuses mock/synthetic deployments, the wrong candidate, expanded namespaces or larger configured budgets. It refuses non-local URLs, redirects and output overwrites. A private `--token-file` may supply the team token instead of its environment variable. Polling has a deadline; timeout requests cancellation and stops later cases. Partial failures are retained in private output; no automatic retry occurs. Review outputs before sharing despite application redaction.

## Real-evidence replay and review

The [captured reports](../evals/real-evidence/2026-11-02-mock-reports.json) contain real collected evidence from disposable samples with mock interpretations, including current/previous logs and ownership. Their [acceptance provenance](acceptance/2026-11-02-optional-evidence-mock.json) identifies the tested revision and image. Replay validates terminal report structure and references without contacting Kubernetes or a provider:

```sh
.venv-source/bin/python scripts/evaluate.py \
  --replay evals/real-evidence/2026-11-02-mock-reports.json \
  --output .data/replay-NEW-RUN.json
```

Replay is not live inference or an accuracy benchmark. Live outputs retain prompt version, case-file hash, configured/returned model, timestamps, evidence, failures and reported token usage. Human reviewers must label incorrect diagnoses, unsupported claims and acceptable outcomes, including ambiguity and healthy cases. Null labels are unreviewed, never passes. Compute quality rates only after reviewing every case and recording the actual dataset, conditions and model identity.

Usage metrics report tokens when supplied; cost estimates in application reports remain unavailable. Infrastructure may cost money even though the code is open source. Redaction, shared-team trust and provider disclosures remain essential for every deployment.
