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

variable "llm_provider" {
  description = "Answer provider for the deployed service."
  type        = string
  default     = "mock"

  validation {
    condition     = contains(["mock", "gemini", "openai"], var.llm_provider)
    error_message = "llm_provider must be one of: mock, gemini, openai."
  }
}

variable "gemini_api_key_secret" {
  description = "Secret Manager secret ID containing the Gemini API key. Required when llm_provider is gemini."
  type        = string
  default     = ""
}

variable "gemini_model" {
  description = "Gemini model name."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "gemini_timeout_seconds" {
  description = "Gemini request timeout in seconds."
  type        = number
  default     = 20
}

variable "gemini_max_output_tokens" {
  description = "Maximum Gemini output tokens."
  type        = number
  default     = 500
}

variable "allow_unauthenticated" {
  description = "Allow public unauthenticated access to the Cloud Run service."
  type        = bool
  default     = true
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
