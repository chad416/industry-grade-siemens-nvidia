data "google_project" "current" {
  project_id = var.project_id
}

resource "google_billing_budget" "monthly" {
  count           = var.billing_account_id == null ? 0 : 1
  billing_account = var.billing_account_id
  display_name    = "${var.name_prefix}-monthly-budget"
  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(floor(var.monthly_budget_amount))
    }
  }
  budget_filter {
    projects = ["projects/${data.google_project.current.number}"]
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
    disable_default_iam_recipients = false
  }
}
