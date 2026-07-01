# Billing and quotas

Billing profiles define usage limits for workspaces. A quota profile can be attached to a
project, deployment environment, or pipeline template. The UI sometimes labels these as
cost guards.

## Included demo quota

The demo quota profile is intended for evaluation environments:

| Limit | Demo value |
| --- | --- |
| Cloud Run max instances | 2 |
| Pipeline runs per day | 20 |
| Artifact storage warning | 1 GB |
| Monthly spend alert | 10 USD |

The demo quota does not create a Google Cloud budget automatically. Customers should create
a cloud budget alert in their own billing account before running public demos.

## Usage reports

Usage reports show deployment count, pipeline run count, artifact storage, failed jobs, and
estimated request cost. Reports are delayed by up to two hours.

If a number in usage reports does not match the cloud provider console, check the report
time window first. The cloud console can include resources created outside Acme CloudOps.

## Quota failures

When a quota limit is reached, new pipeline runs are blocked and deployments pause before
creating a new Cloud Run revision. Existing services keep serving traffic.

The API returns `quota_exceeded` with the quota name, limit, current usage, and reset time.

## Cost controls for Cloud Run demos

For a low-cost demo, set Cloud Run minimum instances to `0`, use a small container, keep max
instances low, delete old Artifact Registry images, and destroy Terraform resources after
the walkthrough.
