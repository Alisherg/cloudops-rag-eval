# FAQ

## Is Acme CloudOps a managed vector database?

No. Acme CloudOps stores product metadata, deployment history, and pipeline artifacts. It can
connect to vector search systems for model applications, but it is not itself a managed vector
database.

## Can Acme deploy to Kubernetes?

Acme CloudOps does not deploy to customer-managed Kubernetes clusters in the standard product.
Cloud Run is the supported HTTP model service target for the demo environment. Custom
integrations may be built outside the standard deployment workflow.

## How are Cloud Run costs controlled?

Use minimum instances of `0`, keep maximum instances low, clean up Artifact Registry images,
and destroy demo infrastructure after the walkthrough. Usage reports in Acme are estimates;
the cloud billing console remains the source of truth.

## Are pipeline evaluation reports the same as retrieval evaluation?

No. Pipeline evaluation reports measure ML model quality before deployment. Retrieval
evaluation measures whether a document-QA system found the right sources and answered only
from those sources.

## Can users share tokens with support?

No. Users should share request IDs, correlation IDs, timestamps, and workspace IDs. They
should not share API tokens, passwords, or private keys.

## What should the assistant do for unsupported topics?

The assistant should refuse to invent details. It should say the docs do not cover the topic
or that the requested deployment target is unsupported, then cite the nearest relevant source
when one exists.
