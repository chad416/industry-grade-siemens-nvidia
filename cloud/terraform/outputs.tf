output "vpc_name" { value = google_compute_network.lab.name }
output "subnet_name" { value = google_compute_subnetwork.lab.name }
output "artifact_bucket" { value = google_storage_bucket.artifacts.name }
output "windows_vm_name" { value = try(google_compute_instance.windows[0].name, null) }
output "gpu_vm_name" { value = try(google_compute_instance.gpu[0].name, null) }
output "cost_warning" { value = "Budget alerts do not cap spend; stopped VMs can retain disk/snapshot/storage/NAT/logging costs." }
