locals {
  required_apis = toset([
    "billingbudgets.googleapis.com", "compute.googleapis.com", "iap.googleapis.com",
    "iam.googleapis.com", "logging.googleapis.com", "monitoring.googleapis.com",
    "serviceusage.googleapis.com", "storage.googleapis.com"
  ])
}

resource "google_project_service" "required" {
  for_each           = local.required_apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "lab" {
  name                    = "${var.name_prefix}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
  depends_on              = [google_project_service.required]
}

resource "google_compute_subnetwork" "lab" {
  name                     = "${var.name_prefix}-subnet"
  region                   = var.region
  network                  = google_compute_network.lab.id
  ip_cidr_range            = var.subnet_cidr
  private_ip_google_access = true
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_router" "lab" {
  name    = "${var.name_prefix}-router"
  region  = var.region
  network = google_compute_network.lab.id
}
resource "google_compute_router_nat" "lab" {
  name                               = "${var.name_prefix}-nat"
  router                             = google_compute_router.lab.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
  subnetwork {
    name                    = google_compute_subnetwork.lab.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

resource "google_compute_firewall" "iap_admin" {
  name      = "${var.name_prefix}-iap-admin"
  network   = google_compute_network.lab.name
  direction = "INGRESS"
  priority  = 1000
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["fc01-iap-admin"]
  allow {
    protocol = "tcp"
    ports    = ["22", "3389"]
  }
  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "egress_dns" {
  name               = "${var.name_prefix}-egress-dns"
  network            = google_compute_network.lab.name
  direction          = "EGRESS"
  priority           = 900
  destination_ranges = ["0.0.0.0/0"]
  allow {
    protocol = "udp"
    ports    = ["53", "123"]
  }
  allow {
    protocol = "tcp"
    ports    = ["53"]
  }
}
resource "google_compute_firewall" "egress_tls" {
  name               = "${var.name_prefix}-egress-tls"
  network            = google_compute_network.lab.name
  direction          = "EGRESS"
  priority           = 910
  destination_ranges = ["0.0.0.0/0"]
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}
resource "google_compute_firewall" "egress_deny" {
  name               = "${var.name_prefix}-egress-deny"
  network            = google_compute_network.lab.name
  direction          = "EGRESS"
  priority           = 65534
  destination_ranges = ["0.0.0.0/0"]
  deny {
    protocol = "all"
  }
  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_storage_bucket" "artifacts" {
  name                        = var.artifact_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  versioning {
    enabled = true
  }
  lifecycle_rule {
    condition {
      age        = 365
      with_state = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }
  labels = var.labels
}
