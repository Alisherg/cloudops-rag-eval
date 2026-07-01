# Troubleshooting

This guide collects common operational issues. Some deployment issues are also described in
the Cloud Run guide, so search both documents when a release fails.

## Startup loop after deploy

Symptoms:

- Cloud Run revision never becomes ready
- logs show repeated container exits
- deployment status remains `pending`

Check that the service listens on the `PORT` environment variable, starts within the timeout,
and does not require a local file that is missing from the image.

## Artifact access denied

If a model service cannot read `gs://` artifacts, verify that the runtime service account has
object viewer access on the bucket. Also confirm the artifact path exists and was produced by
the latest successful pipeline run.

The pipelines guide calls this an artifact permission failure. The deployment page may show
it as model artifact unavailable.

## Token rejected

If an API token is rejected:

1. Confirm the token was not copied with whitespace.
2. Check whether it was rotated or revoked.
3. Verify the token has the required scope.
4. Use the workspace ID from the same account that created the token.

Do not paste tokens into support tickets. Share the request ID and correlation ID instead.

## Quota warning looks wrong

Quota reports can lag by up to two hours. If a quota warning appears after resources were
deleted, wait for the next report window and compare the environment filter.

## Unsupported request

If a user asks Acme to deploy desktop agents, unmanaged Kubernetes clusters, or legal
compliance documents, the correct response is to say the topic is not supported by the
product docs and cite the nearest relevant documentation.
