param([Parameter(Mandatory=$true)][string]$VarFile, [string]$OutputDirectory = "")
$ErrorActionPreference = 'Stop'
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) { throw 'Terraform CLI is not installed or approved' }
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\terraform')).Path
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path.TrimEnd('\') + '\'
if (-not (Test-Path -LiteralPath $VarFile -PathType Leaf)) { throw "Variable file does not exist: $VarFile" }
$resolvedVarFile = (Resolve-Path -LiteralPath $VarFile).Path
if (-not $OutputDirectory) { $OutputDirectory = Join-Path ([IO.Path]::GetTempPath()) ('fc01-cloud-plan-' + [Guid]::NewGuid().ToString('N')) }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$outputRoot = (Resolve-Path -LiteralPath $OutputDirectory).Path
if (($outputRoot.TrimEnd('\') + '\').StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Cloud plan output must remain outside the controlled release tree'
}
$workRoot = Join-Path $outputRoot 'terraform-work'
if (Test-Path -LiteralPath $workRoot) { throw "Refusing to overwrite existing work directory: $workRoot" }
New-Item -ItemType Directory -Path $workRoot | Out-Null
Copy-Item -Path (Join-Path $sourceRoot '*') -Destination $workRoot -Recurse
Push-Location $workRoot
try {
  terraform fmt -check -recursive
  terraform init -backend=false -input=false
  terraform validate
  $plan = Join-Path $outputRoot 'fc01-revision-g.tfplan'
  terraform plan -input=false -refresh=false -lock=false -var-file=$resolvedVarFile -out=$plan
  $planText = Join-Path $outputRoot 'fc01-revision-g-plan.txt'
  terraform show -no-color $plan | Set-Content -Encoding utf8 $planText
  Get-FileHash -Algorithm SHA256 $plan,$planText
} finally { Pop-Location }
Write-Output 'NO APPLY WAS RUN. Review the plan and cost separately.'
