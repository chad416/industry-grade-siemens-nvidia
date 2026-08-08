variable "project_id" {
  type = string
}
variable "billing_account_id" {
  type    = string
  default = null
}
variable "region" {
  type    = string
  default = "europe-west4"
}
variable "zone" {
  type    = string
  default = "europe-west4-a"
}
variable "name_prefix" {
  type    = string
  default = "fc01-lab"
}
variable "subnet_cidr" {
  type    = string
  default = "10.71.0.0/24"
}
variable "admin_principals" {
  type    = set(string)
  default = []
}
variable "operator_principals" {
  type    = set(string)
  default = []
}
variable "create_windows_vm" {
  type    = bool
  default = false
}
variable "create_gpu_vm" {
  type    = bool
  default = false
}
variable "windows_machine_type" {
  type    = string
  default = "n2-standard-8"
}
variable "gpu_machine_type" {
  type    = string
  default = "g2-standard-4"
}
variable "windows_boot_image" {
  type    = string
  default = "projects/windows-cloud/global/images/family/windows-2022"
}
variable "gpu_boot_image" {
  type    = string
  default = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2404-lts-amd64"
}
variable "artifact_bucket_name" {
  type = string
}
variable "monthly_budget_amount" {
  type    = number
  default = 250
}
variable "schedule_time_zone" {
  type    = string
  default = "Europe/Berlin"
}
variable "monitoring_notification_channels" {
  type    = list(string)
  default = []
}
variable "labels" {
  type = map(string)
  default = {
    system      = "fc01"
    environment = "engineering-lab"
    managed_by  = "terraform"
  }
}
