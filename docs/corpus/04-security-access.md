# Security and access

Acme CloudOps uses role-based access control for workspaces and projects. Customers manage
identity through SSO, local invites, or service accounts for automation.

## User roles

Owners can manage billing, users, service connections, and production deployment settings.
Maintainers can edit pipelines and deploy to non-production environments. Operators can view
deployments, acknowledge incidents, and trigger approved rollbacks. Viewers can read reports
and deployment history.

Maintainers cannot change billing settings. Operators cannot create new API tokens.

## API tokens

API tokens are scoped to a workspace and can be limited to a project. Tokens are shown once
when created. Store them in a secret manager and rotate them every 90 days.

Token scopes:

| Scope | Allows |
| --- | --- |
| `documents:read` | Read docs and run search |
| `pipelines:write` | Start and retry pipelines |
| `deployments:write` | Create deployment candidates and rollbacks |
| `billing:read` | View quota and usage reports |

Never send API tokens in query strings. Use the `Authorization: Bearer` header.

## Audit logging

Acme records audit events for login, token creation, role changes, deployment approval,
rollback, and billing profile changes. Logs include actor, workspace, project, timestamp,
and correlation ID.

## Data handling

The platform masks access tokens, API keys, passwords, and email addresses in application
logs. Raw request bodies are not retained by default.

## Unsupported security topics

Acme CloudOps does not provide legal compliance certification advice. The security team can
export audit logs, but customers are responsible for their own compliance review.
