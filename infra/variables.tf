variable "project_id" {
  description = "Google Cloud project ID."
  type        = string
}

variable "region" {
  description = "Google Cloud region for Cloud Run and Artifact Registry."
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name."
  type        = string
  default     = "cloudops-rag-eval"
}

variable "artifact_repo_id" {
  description = "Artifact Registry repository ID."
  type        = string
  default     = "cloudops-rag-eval"
}

variable "image" {
  description = "Container image URI to deploy."
  type        = string
}

variable "allow_unauthenticated" {
  description = "Allow public unauthenticated access to the Cloud Run service."
  type        = bool
  default     = true
}

variable "create_docs_bucket" {
  description = "Create a small optional bucket for source documents."
  type        = bool
  default     = false
}

variable "docs_bucket_name" {
  description = "Optional Cloud Storage bucket name. Leave empty to derive one."
  type        = string
  default     = ""
}

variable "budget_billing_account_id" {
  description = "Billing account ID for an optional budget alert. Leave empty to skip."
  type        = string
  default     = ""
}

variable "budget_alert_email" {
  description = "Email address for an optional budget notification channel."
  type        = string
  default     = ""
}

variable "budget_amount_usd" {
  description = "Monthly demo budget amount in USD."
  type        = number
  default     = 10
}
