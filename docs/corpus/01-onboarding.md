# Acme CloudOps Platform onboarding

Acme CloudOps Platform is a fictional cloud-native operations product for small ML teams.
It helps teams package model services, run pipeline jobs, track deployment checks, and keep
cost controls visible before a release reaches production.

## Workspace setup

Each customer starts with one workspace. A workspace contains projects, service connections,
API tokens, pipeline templates, and deployment environments.

| Role | Typical owner | Can invite users |
| --- | --- | --- |
| Owner | Platform lead | Yes |
| Maintainer | ML engineer | Yes |
| Operator | On-call engineer | No |
| Viewer | Auditor or stakeholder | No |

The first Owner should create a project, add a service connection, and choose a default
deployment region. For GCP demos, the recommended region is `us-central1` because it keeps
Cloud Run and optional Cloud Storage settings simple.

## Environment terms

The product uses the terms environment, runtime target, and deployment lane in different
screens. They usually refer to the same release boundary. In API responses the field is
called `environment`.

Common environments are:

- `dev` for local and pull request previews
- `staging` for shared validation
- `prod` for customer-facing services

## First deployment checklist

Before a first deployment, confirm that:

- the model artifact was published by a pipeline run
- the service account can read the artifact location
- the environment has a quota profile
- the Cloud Run deployment target has request logging enabled
- the rollback policy names a previous stable revision

The onboarding checklist sometimes calls the rollback policy a recovery policy. The API and
deployment docs use rollback policy.

## Unsupported onboarding requests

Acme CloudOps does not onboard unmanaged on-prem clusters, customer-hosted Kubernetes
control planes, or desktop agents. Teams that need those targets should use a custom
integration outside Acme CloudOps.
