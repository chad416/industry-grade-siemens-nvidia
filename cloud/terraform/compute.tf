resource "google_compute_resource_policy" "weekday_schedule" {
  name   = "${var.name_prefix}-weekday-schedule"
  region = var.region
  instance_schedule_policy {
    vm_start_schedule {
      schedule = "0 8 * * MON-FRI"
    }
    vm_stop_schedule {
      schedule = "0 18 * * MON-FRI"
    }
    time_zone = var.schedule_time_zone
  }
}

resource "google_compute_disk" "windows_data" {
  count                     = var.create_windows_vm ? 1 : 0
  name                      = "${var.name_prefix}-windows-data"
  type                      = "pd-balanced"
  zone                      = var.zone
  size                      = 200
  physical_block_size_bytes = 4096
  labels                    = var.labels
}
resource "google_compute_disk" "gpu_data" {
  count                     = var.create_gpu_vm ? 1 : 0
  name                      = "${var.name_prefix}-gpu-data"
  type                      = "pd-balanced"
  zone                      = var.zone
  size                      = 500
  physical_block_size_bytes = 4096
  labels                    = var.labels
}

resource "google_compute_instance" "windows" {
  count               = var.create_windows_vm ? 1 : 0
  name                = "${var.name_prefix}-windows"
  machine_type        = var.windows_machine_type
  zone                = var.zone
  deletion_protection = true
  tags                = ["fc01-iap-admin", "fc01-windows"]
  labels              = var.labels
  boot_disk {
    initialize_params {
      image = var.windows_boot_image
      size  = 150
      type  = "pd-balanced"
    }
  }
  attached_disk {
    source = google_compute_disk.windows_data[0].id
    mode   = "READ_WRITE"
  }
  network_interface {
    subnetwork = google_compute_subnetwork.lab.id
  }
  service_account {
    email  = google_service_account.windows.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  resource_policies = [google_compute_resource_policy.weekday_schedule.id]
  metadata = {
    enable-osconfig    = "TRUE"
    serial-port-enable = "FALSE"
  }
  lifecycle {
    prevent_destroy = true
  }
}

resource "google_compute_instance" "gpu" {
  count               = var.create_gpu_vm ? 1 : 0
  name                = "${var.name_prefix}-gpu"
  machine_type        = var.gpu_machine_type
  zone                = var.zone
  deletion_protection = true
  tags                = ["fc01-iap-admin", "fc01-nvidia"]
  labels              = var.labels
  boot_disk {
    initialize_params {
      image = var.gpu_boot_image
      size  = 100
      type  = "pd-balanced"
    }
  }
  attached_disk {
    source = google_compute_disk.gpu_data[0].id
    mode   = "READ_WRITE"
  }
  network_interface {
    subnetwork = google_compute_subnetwork.lab.id
  }
  service_account {
    email  = google_service_account.nvidia.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = false
    preemptible          = false
  }
  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  resource_policies = [google_compute_resource_policy.weekday_schedule.id]
  metadata = {
    enable-osconfig       = "TRUE"
    install-nvidia-driver = "TRUE"
    serial-port-enable    = "FALSE"
  }
  lifecycle {
    prevent_destroy = true
  }
}
