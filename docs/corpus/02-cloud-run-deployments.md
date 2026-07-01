# Cloud Run deployment guide

Acme CloudOps can deploy HTTP model services to Google Cloud Run. The platform builds a
container image, attaches the chosen service account, sets environment variables, and records
the Cloud Run revision in the deployment history.

## Deployment target

A deployment target joins an Acme environment to a Cloud Run service. The target stores:

- GCP project ID
- region
- service name
- Artifact Registry image repository
- service account email
- max instance count

For demos, set minimum instances to `0` and maximum instances to `2`. This keeps the service
cheap while still showing autoscaling behavior.

## Required variables

The runtime container must expose an HTTP server on the `PORT` value provided by Cloud Run.
Acme injects these variables during deployment:

| Variable | Example | Notes |
| --- | --- | --- |
| `ACME_ENVIRONMENT` | `staging` | Same value as the release environment |
| `ACME_DEPLOYMENT_ID` | `dep_01hxy` | Used for trace lookup |
| `ACME_MODEL_ARTIFACT` | `gs://bucket/model.tar` | Required for model services |

Application teams can add their own variables, but secrets should be referenced from the
workspace secret store rather than pasted into deployment settings.

## Rollbacks

A rollback redeploys a previously healthy Cloud Run revision. The release page calls this
"restore previous version"; the deployment API calls it `rollback_revision`.

Rollback is blocked when the previous revision used a deleted secret, a removed service
account, or a model artifact that no longer exists.

## Deployment troubleshooting

If a Cloud Run service returns 503 immediately after deployment, check the container port,
startup timeout, and service account permissions. The troubleshooting guide has additional
steps for artifact access errors and startup loops.
