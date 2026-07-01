# ML pipelines

Pipelines in Acme CloudOps package repeatable ML operations such as data validation, feature
checks, model training, evaluation, approval, and deployment handoff. The pipeline runner is
managed by Acme and does not require customer VMs.

## Pipeline stages

A standard pipeline has these stages:

1. Ingest metadata
2. Validate schema
3. Train or import a model
4. Run evaluation checks
5. Publish an artifact
6. Create a deployment candidate

The stage named evaluation is unrelated to the RAG evaluation harness in this repository.
In product docs, evaluation usually means model quality gates for ML pipelines.

## Artifacts

Pipeline artifacts include model files, metrics reports, feature statistics, and approval
records. A deployment candidate must reference one model artifact and one evaluation report.

Artifacts can be stored in an Acme-managed bucket or in customer Cloud Storage. Customer
buckets require a service account grant with object read access.

## Approval gates

Approval gates can check:

- minimum accuracy or F1 score
- maximum latency
- cost estimate per 10,000 requests
- required reviewer sign-off

Failed gates keep the deployment candidate in `blocked` state. The candidate can be retried
after the pipeline publishes a newer evaluation report.

## Pipeline failures

Pipeline failures are usually caused by missing artifact permissions, schema drift, or quota
profile limits. Deployment failures after a successful pipeline are covered in the Cloud Run
guide and troubleshooting guide.
