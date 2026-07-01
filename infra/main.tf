locals {
  docs_bucket_name = var.docs_bucket_name != "" ? var.docs_bucket_name : "${var.project_id}-${var.service_name}-docs"
  budget_enabled   = var.budget_billing_account_id != "" && var.budget_alert_email != ""
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_service" "required" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "billingbudgets.googleapis.com",
    "monitoring.googleapis.com",
    "run.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = var.artifact_repo_id
  description   = "Docker images for ${var.service_name}"
  format        = "DOCKER"

  cleanup_policies {
    id     = "delete-untagged-after-seven-days"
    action = "DELETE"

    condition {
      tag_state  = "UNTAGGED"
      older_than = "604800s"
    }
  }

  cleanup_policies {
    id     = "keep-last-three-tagged"
    action = "KEEP"

    most_recent_versions {
      keep_count = 3
    }
  }

  depends_on = [google_project_service.required]
}

resource "google_service_account" "cloud_run" {
  account_id   = "${var.service_name}-run"
  display_name = "${var.service_name} Cloud Run"

  depends_on = [google_project_service.required]
}

resource "google_cloud_run_v2_service" "app" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = var.image

      ports {
        container_port = 8080
      }

      env {
        name  = "APP_ENV"
        value = "cloud"
      }

      env {
        name  = "LLM_PROVIDER"
        value = "mock"
      }

      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }

      env {
        name  = "CHROMA_PATH"
        value = "/tmp/cloudops-rag-eval/chroma"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }

        cpu_idle          = true
        startup_cpu_boost = true
      }
    }
  }

  depends_on = [
    google_artifact_registry_repository.app,
    google_project_service.required,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count    = var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.app.name
  location = google_cloud_run_v2_service.app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_storage_bucket" "docs" {
  count                       = var.create_docs_bucket ? 1 : 0
  name                        = local.docs_bucket_name
  location                    = upper(var.region)
  uniform_bucket_level_access = true
  force_destroy               = true

  versioning {
    enabled = false
  }
}

resource "google_monitoring_notification_channel" "budget_email" {
  count        = local.budget_enabled ? 1 : 0
  display_name = "${var.service_name} budget email"
  type         = "email"

  labels = {
    email_address = var.budget_alert_email
  }

  depends_on = [google_project_service.required]
}

resource "google_billing_budget" "demo" {
  count           = local.budget_enabled ? 1 : 0
  billing_account = var.budget_billing_account_id
  display_name    = "${var.service_name} demo budget"

  budget_filter {
    projects               = ["projects/${data.google_project.current.number}"]
    credit_types_treatment = "INCLUDE_ALL_CREDITS"
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.budget_amount_usd)
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }

  threshold_rules {
    threshold_percent = 0.8
  }

  threshold_rules {
    threshold_percent = 1.0
  }

  all_updates_rule {
    monitoring_notification_channels = [google_monitoring_notification_channel.budget_email[0].id]
    disable_default_iam_recipients   = false
  }

  depends_on = [google_project_service.required]
}
