output "artifact_repository" {
  description = "Artifact Registry repository URI prefix."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

output "cloud_run_url" {
  description = "Cloud Run service URL."
  value       = google_cloud_run_v2_service.app.uri
}

output "docs_bucket" {
  description = "Optional source document bucket."
  value       = var.create_docs_bucket ? google_storage_bucket.docs[0].name : null
}
