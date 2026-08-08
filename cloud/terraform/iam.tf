resource "google_service_account" "windows" {
  account_id   = "${var.name_prefix}-windows"
  display_name = "FC01 Windows engineering VM"
  description  = "Keyless workload identity; no project-owner grant"
}
resource "google_service_account" "nvidia" {
  account_id   = "${var.name_prefix}-nvidia"
  display_name = "FC01 NVIDIA engineering VM"
  description  = "Keyless workload identity; no project-owner grant"
}

resource "google_project_iam_member" "windows_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.windows.email}"
}
resource "google_project_iam_member" "windows_metrics" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.windows.email}"
}
resource "google_project_iam_member" "nvidia_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.nvidia.email}"
}
resource "google_project_iam_member" "nvidia_metrics" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.nvidia.email}"
}
resource "google_storage_bucket_iam_member" "windows_artifacts" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.windows.email}"
}
resource "google_storage_bucket_iam_member" "nvidia_artifacts" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.nvidia.email}"
}

resource "google_project_iam_member" "iap_admin" {
  for_each = var.admin_principals
  project  = var.project_id
  role     = "roles/iap.tunnelResourceAccessor"
  member   = each.value
}

resource "google_project_iam_custom_role" "vm_operator" {
  role_id     = "fc01LabVmOperator"
  title       = "FC01 Lab VM Operator"
  description = "Start, stop and inspect FC01 lab VMs without broad instance administration"
  permissions = ["compute.instances.get", "compute.instances.list", "compute.instances.start", "compute.instances.stop", "compute.zoneOperations.get"]
}
resource "google_project_iam_member" "vm_operator" {
  for_each = var.operator_principals
  project  = var.project_id
  role     = google_project_iam_custom_role.vm_operator.name
  member   = each.value
}
