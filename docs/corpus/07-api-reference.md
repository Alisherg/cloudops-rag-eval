# API reference

The Acme CloudOps API is organized around workspaces, projects, pipelines, deployments, and
documents. All examples use fictional identifiers.

## Authentication

Send API tokens with the `Authorization: Bearer <token>` header. Tokens require scopes for
the endpoint being called.

Common error codes:

| Code | Meaning |
| --- | --- |
| `invalid_token` | Token is missing, expired, revoked, or malformed |
| `permission_denied` | Token exists but lacks the required scope |
| `quota_exceeded` | Quota profile blocked the request |
| `not_found` | Workspace, project, artifact, or deployment was not found |

## Create deployment candidate

`POST /v1/deployments`

Request fields:

- `workspace_id`
- `project_id`
- `environment`
- `model_artifact_uri`
- `evaluation_report_id`
- `target`

The target must refer to a configured runtime target such as Cloud Run. The response includes
`deployment_id`, `status`, and `correlation_id`.

## Start pipeline

`POST /v1/pipelines/{pipeline_id}/runs`

The request may include a branch name, data snapshot, and run parameters. The response returns
`run_id`, `status`, and a link to the evaluation report once available.

## Search documents

`POST /v1/documents/search`

Document search accepts a plain text query and returns matching snippets. Search is intended
for product docs and runbooks, not customer data discovery.
