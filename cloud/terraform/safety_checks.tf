check "approved_access_before_compute" {
  assert {
    condition     = !(var.create_windows_vm || var.create_gpu_vm) || length(var.admin_principals) > 0
    error_message = "At least one approved IAP administrator principal is required before VM creation."
  }
}

check "budget_before_compute" {
  assert {
    condition     = !(var.create_windows_vm || var.create_gpu_vm) || var.billing_account_id != null
    error_message = "A billing account and budget resource are required before paid compute can be enabled."
  }
}

check "alert_route_before_compute" {
  assert {
    condition     = !(var.create_windows_vm || var.create_gpu_vm) || length(var.monitoring_notification_channels) > 0
    error_message = "At least one approved Monitoring notification channel is required before VM creation."
  }
}
