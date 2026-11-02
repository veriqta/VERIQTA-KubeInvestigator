# Provider and evaluations

Two independent settings matter: `KI_SOURCE=fixture|kubernetes` controls evidence; `KI_PROVIDER=mock|openai` controls interpretation. Fixture requires mock. Mock requires no API key and never contacts a model provider. Reports and captures explicitly label mock and synthetic evidence separately.

The live adapter implements the OpenAI Chat Completions JSON-mode contract with `max_completion_tokens=1600`, a fixed api.openai.com destination, no redirects, no automatic retries, and a 20-second HTTP timeout within the investigation deadline. Errors for authentication, rate limits, unsupported models, invalid JSON, malformed tools, invented references and timeouts become failed reports with retained evidence. Failure does not silently switch to mock. The tested provider contract uses a synthetic HTTP transport in tests; **no live model configuration has been tested**. The default candidate is `gpt-4.1-mini`, configurable with KI_MODEL. Review [official model availability](https://developers.openai.com/api/docs/models/gpt-4.1-mini) before live use, including announced deprecations. Do not assume access through a ChatGPT subscription; API billing is separate.

Use an existing Kubernetes Secret with keys KI_TOKEN and KI_API_KEY. Create the Secret from a private env file or your secret manager, never Helm values or source control. Set chart `provider=openai` and `model` to your authorised model. For local restricted-kubeconfig operation set KI_SOURCE=kubernetes, KI_PROVIDER=openai and KI_API_KEY in the server environment. No key is embedded in JavaScript or exports.

Opt-in live evaluation (this performs paid calls and requires your independent authorisation):

```sh
# Point at an authorised deployment configured with the live provider.
# KI_TOKEN is the team token; provider credentials exist only on the server.
.venv/bin/python scripts/evaluate.py --acknowledge-paid-calls --url http://127.0.0.1:8080
```

Use a dedicated sample environment from the demo guide with its failure state reset; do not evaluate production workloads. Six cases cover supported conditions, a healthy pod, ambiguity without logs and an unsupported latency/remediation request. Each defines expected evidence and acceptable limitations in [cases](../evals/cases.json). Output records UTC time, software/model configuration, prompt version, complete redacted reports and review fields. A human must label incorrect diagnosis, unsupported claims and acceptable outcome; null is not a pass. Count those errors as well as successful cases and preserve conditions and operator-reviewed results. Prompt text is versioned in provider.py. No accuracy benchmark or coverage claim has been established.

Usage is recorded when supplied by OpenAI and aggregated in metrics. Estimated cost is null because reliable billed usage/pricing is not established. No live calls were made, so observed live-provider cost is unavailable. Budget for up to six calls per investigation with repeated context and up to 1600 output tokens per call; check your provider price sheet and billing controls. A live evaluation can create six investigations. Infrastructure and paid model access can cost money even though the software is open source.
