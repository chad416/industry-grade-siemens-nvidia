$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RuntimeRoot = 'C:\Users\chand\.cache\codex-runtimes\codex-primary-runtime\dependencies'
$Python = Join-Path $RuntimeRoot 'python\python.exe'
$Node = Join-Path $RuntimeRoot 'node\bin\node.exe'
$NodeModules = Join-Path $RuntimeRoot 'node\node_modules'
$Poppler = Join-Path $RuntimeRoot 'native\poppler\Library\bin'
$BuildJunction = Join-Path $ProjectRoot 'node_modules'

function Invoke-Native {
    param([Parameter(Mandatory=$true)][string]$Executable, [Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Native command failed ($LASTEXITCODE): $Executable $($Arguments -join ' ')" }
}

function Reset-GeneratedDirectory {
    param([Parameter(Mandatory=$true)][string]$RelativePath)
    $Target = [IO.Path]::GetFullPath((Join-Path $ProjectRoot $RelativePath))
    $RootPrefix = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\') + '\'
    if (-not $Target.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Refusing to reset path outside project: $Target" }
    if (-not (Test-Path -LiteralPath $Target)) {
        New-Item -ItemType Directory -Path $Target | Out-Null
        return
    }
    foreach ($Child in Get-ChildItem -LiteralPath $Target -Force) {
        $Removed = $false
        for ($Attempt = 1; $Attempt -le 20; $Attempt++) {
            try {
                Remove-Item -LiteralPath $Child.FullName -Recurse -Force
                $Removed = $true
                break
            }
            catch {
                if ($Attempt -eq 20) { throw }
                Start-Sleep -Milliseconds 250
            }
        }
        if (-not $Removed) { throw "Unable to remove generated item: $($Child.FullName)" }
    }
    if ((Get-ChildItem -LiteralPath $Target -Force | Measure-Object).Count -ne 0) {
        throw "Generated directory is not empty after reset: $Target"
    }
}

Push-Location $ProjectRoot
try {
    Reset-GeneratedDirectory '14_qa\pdf_renders\release'
    Reset-GeneratedDirectory '14_qa\pdf_renders\release_c'
    Invoke-Native $Python 'scripts\build_project.py'
    Invoke-Native $Python '-m' 'unittest' 'discover' '-s' '11_simulation\tests' '-v'
    Invoke-Native $Python '11_simulation\run_scenarios.py'
    Invoke-Native $Python '-m' 'unittest' 'discover' '-s' '07_nvidia_vision\edge_service\tests' '-v'
    Push-Location '07_nvidia_vision'
    try { Invoke-Native $Python '-m' 'unittest' '-v' 'test_plc_interface_harness.py' } finally { Pop-Location }
    Invoke-Native $Python 'scripts\check_determinism.py'

    if (Test-Path -LiteralPath $BuildJunction) {
        $Existing = Get-Item -LiteralPath $BuildJunction -Force
        if ($Existing.LinkType -ne 'Junction' -or $Existing.Target -notcontains $NodeModules) { throw 'Unexpected node_modules path; refusing to overwrite it' }
    } else {
        New-Item -ItemType Junction -Path $BuildJunction -Target $NodeModules | Out-Null
    }
    try {
        Invoke-Native $Node 'scripts\build_workbook.mjs'
        Invoke-Native $Python 'scripts\normalize_xlsx.py'
        $WorkbookHash1 = (Get-FileHash -Algorithm SHA256 '10_schedules\FC01_engineering_schedules.xlsx').Hash
        Invoke-Native $Node 'scripts\build_workbook.mjs'
        Invoke-Native $Python 'scripts\normalize_xlsx.py'
        $WorkbookHash2 = (Get-FileHash -Algorithm SHA256 '10_schedules\FC01_engineering_schedules.xlsx').Hash
        if ($WorkbookHash1 -ne $WorkbookHash2) { throw "Normalized workbook is not binary deterministic: $WorkbookHash1 != $WorkbookHash2" }
    }
    finally {
        if (Test-Path -LiteralPath $BuildJunction) {
            $Item = Get-Item -LiteralPath $BuildJunction -Force
            if ($Item.LinkType -eq 'Junction' -and $Item.Target -contains $NodeModules) { [IO.Directory]::Delete($BuildJunction, $false) }
        }
    }
    Invoke-Native $Python 'scripts\build_contact_sheets.py'

    Invoke-Native $Python 'scripts\build_release_pdf.py'
    $PdfHash1 = (Get-FileHash -Algorithm SHA256 'release\FC01_release_evidence.pdf').Hash
    Invoke-Native $Python 'scripts\build_release_pdf.py'
    $PdfHash2 = (Get-FileHash -Algorithm SHA256 'release\FC01_release_evidence.pdf').Hash
    if ($PdfHash1 -ne $PdfHash2) { throw "Release PDF is not binary deterministic: $PdfHash1 != $PdfHash2" }
    Reset-GeneratedDirectory '14_qa\pdf_renders\release_d'
    Invoke-Native (Join-Path $Poppler 'pdftoppm.exe') '-png' '-r' '140' 'release\FC01_release_evidence.pdf' '14_qa\pdf_renders\release_d\page'
    $PdfRenderNames = @(Get-ChildItem '14_qa\pdf_renders\release_d' -File | Sort-Object Name | ForEach-Object Name)
    $ExpectedPdfRenderNames = @(1..5 | ForEach-Object { "page-$_.png" })
    if (Compare-Object $ExpectedPdfRenderNames $PdfRenderNames) { throw 'PDF render set is not exactly pages 1 through 5' }
    Invoke-Native $Python 'scripts\build_pdf_contact_sheets.py'

    Invoke-Native $Python 'scripts\validate_project.py'
    Invoke-Native $Python 'scripts\build_manifest.py'
    Invoke-Native $Python 'scripts\verify_manifest.py'
}
finally { Pop-Location }
