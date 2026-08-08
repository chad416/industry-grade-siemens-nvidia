resource "google_project_iam_audit_config" "all_services" {
  project = var.project_id
  service = "allServices"
  audit_log_config {
    log_type = "ADMIN_READ"
  }
  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

resource "google_monitoring_alert_policy" "windows_high_cpu" {
  count                = var.create_windows_vm ? 1 : 0
  display_name         = "${var.name_prefix} Windows sustained high CPU"
  combiner             = "OR"
  notification_channels = var.monitoring_notification_channels
  conditions {
    display_name = "Windows VM CPU above 90 percent for 15 minutes"
    condition_threshold {
      filter          = "resource.type = \"gce_instance\" AND resource.labels.instance_id = \"${google_compute_instance.windows[0].instance_id}\" AND metric.type = \"compute.googleapis.com/instance/cpu/utilization\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.9
      duration        = "900s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  documentation {
    content   = "Investigate the FC01 Windows engineering workload; stop the VM if it is not under an approved active session."
    mime_type = "text/markdown"
  }
}

resource "google_monitoring_alert_policy" "gpu_high_cpu" {
  count                = var.create_gpu_vm ? 1 : 0
  display_name         = "${var.name_prefix} GPU host sustained high CPU"
  combiner             = "OR"
  notification_channels = var.monitoring_notification_channels
  conditions {
    display_name = "GPU host CPU above 90 percent for 15 minutes"
    condition_threshold {
      filter          = "resource.type = \"gce_instance\" AND resource.labels.instance_id = \"${google_compute_instance.gpu[0].instance_id}\" AND metric.type = \"compute.googleapis.com/instance/cpu/utilization\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.9
      duration        = "900s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  documentation {
    content   = "Investigate the FC01 NVIDIA workload and stop the GPU VM when no approved job is active. GPU utilization requires the approved Ops Agent/NVIDIA telemetry setup."
    mime_type = "text/markdown"
  }
}
