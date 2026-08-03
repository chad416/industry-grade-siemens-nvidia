param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$KnownRuntime = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.cache\codex-runtimes\codex-primary-runtime\dependencies'

function Resolve-Executable {
    param(
        [Parameter(Mandatory=$true)][string]$EnvironmentName,
        [Parameter(Mandatory=$true)][string]$KnownRelativePath,
        [Parameter(Mandatory=$true)][string[]]$CommandNames
    )
    $Explicit = [Environment]::GetEnvironmentVariable($EnvironmentName)
    if ($Explicit) {
        if (-not (Test-Path -LiteralPath $Explicit -PathType Leaf)) { throw "$EnvironmentName does not identify a file: $Explicit" }
        return (Resolve-Path -LiteralPath $Explicit).Path
    }
    $Known = Join-Path $KnownRuntime $KnownRelativePath
    if (Test-Path -LiteralPath $Known -PathType Leaf) { return (Resolve-Path -LiteralPath $Known).Path }
    foreach ($Name in $CommandNames) {
        $Command = Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($Command) { return $Command.Source }
    }
    throw "Unable to resolve $EnvironmentName; checked $Known and commands $($CommandNames -join ', ')"
}

function Resolve-Directory {
    param([Parameter(Mandatory=$true)][string]$EnvironmentName, [Parameter(Mandatory=$true)][string]$KnownRelativePath)
    $Explicit = [Environment]::GetEnvironmentVariable($EnvironmentName)
    if ($Explicit) {
        if (-not (Test-Path -LiteralPath $Explicit -PathType Container)) { throw "$EnvironmentName does not identify a directory: $Explicit" }
        return (Resolve-Path -LiteralPath $Explicit).Path
    }
    $Known = Join-Path $KnownRuntime $KnownRelativePath
    if (Test-Path -LiteralPath $Known -PathType Container) { return (Resolve-Path -LiteralPath $Known).Path }
    throw "Unable to resolve $EnvironmentName; set it explicitly on non-Codex release runners"
}

$Python = Resolve-Executable 'FC01_PYTHON' 'python\python.exe' @('python','python3')
$Node = Resolve-Executable 'FC01_NODE' 'node\bin\node.exe' @('node')
$NodeModules = Resolve-Directory 'FC01_NODE_MODULES' 'node\node_modules'
$Pdftoppm = Resolve-Executable 'FC01_PDFTOPPM' 'native\poppler\Library\bin\pdftoppm.exe' @('pdftoppm')
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
    if (-not (Test-Path -LiteralPath $Target)) { New-Item -ItemType Directory -Path $Target | Out-Null; return }
    foreach ($Child in Get-ChildItem -LiteralPath $Target -Force) { Remove-Item -LiteralPath $Child.FullName -Recurse -Force }
    if ((Get-ChildItem -LiteralPath $Target -Force | Measure-Object).Count -ne 0) { throw "Generated directory is not empty after reset: $Target" }
}

function Assert-CleanGitState {
    $Status = @(git status --porcelain=v1 --untracked-files=all)
    if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect Git state' }
    if ($Status.Count -ne 0) { throw "Release worktree is not clean:`n$($Status -join "`n")" }
}

Push-Location $ProjectRoot
try {
    # Integrity preflight occurs before any generation or removal.
    Assert-CleanGitState
    Invoke-Native $Python 'scripts\verify_manifest.py' '--source' 'head' '--require-clean'
    Invoke-Native $Python 'scripts\test_release_integrity.py' '--source' 'head'
    Invoke-Native $Python 'scripts\verify_release_toolchain.py' '--node' $Node '--node-modules' $NodeModules '--pdftoppm' $Pdftoppm
    Invoke-Native $Python 'scripts\validate_project.py' '--check'

    Invoke-Native $Python 'scripts\build_project.py'
    Invoke-Native $Python '-m' 'unittest' 'discover' '-s' '11_simulation\tests' '-v'
    Invoke-Native $Python '11_simulation\run_scenarios.py'
    Invoke-Native $Python '-m' 'unittest' 'discover' '-s' '07_nvidia_vision\edge_service\tests' '-v'
    Push-Location '07_nvidia_vision'
    try { Invoke-Native $Python '-m' 'unittest' '-v' 'test_plc_interface_harness.py' } finally { Pop-Location }
    Invoke-Native $Python 'scripts\check_determinism.py' '--source' 'head'

    if (Test-Path -LiteralPath $BuildJunction) { throw "Unexpected node_modules path exists before workbook build: $BuildJunction" }
    New-Item -ItemType Junction -Path $BuildJunction -Target $NodeModules | Out-Null
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
            else { throw 'Refusing to remove unexpected node_modules path' }
        }
    }
    Invoke-Native $Python 'scripts\build_contact_sheets.py'

    Invoke-Native $Python 'scripts\build_release_pdf.py'
    $PdfHash1 = (Get-FileHash -Algorithm SHA256 'release\FC01_release_evidence.pdf').Hash
    Invoke-Native $Python 'scripts\build_release_pdf.py'
    $PdfHash2 = (Get-FileHash -Algorithm SHA256 'release\FC01_release_evidence.pdf').Hash
    if ($PdfHash1 -ne $PdfHash2) { throw "Release PDF is not binary deterministic: $PdfHash1 != $PdfHash2" }

    Reset-GeneratedDirectory '14_qa\pdf_renders\release_d'
    Invoke-Native $Pdftoppm '-png' '-r' '140' 'release\FC01_release_evidence.pdf' '14_qa\pdf_renders\release_d\page'
    $ReleasePages = @(Get-ChildItem '14_qa\pdf_renders\release_d' -File | Sort-Object Name | ForEach-Object Name)
    $ExpectedReleasePages = @(1..5 | ForEach-Object { "page-$_.png" })
    if (Compare-Object $ExpectedReleasePages $ReleasePages) { throw 'Release PDF render set is not exactly pages 1 through 5' }

    Reset-GeneratedDirectory '14_qa\pdf_renders\qet_baseline'
    Invoke-Native $Pdftoppm '-png' '-r' '140' '03_electrical\native_baseline\filling_cell_schematics.pdf' '14_qa\pdf_renders\qet_baseline\page'
    $QetPages = @(Get-ChildItem '14_qa\pdf_renders\qet_baseline' -File | Sort-Object Name | ForEach-Object Name)
    $ExpectedQetPages = @(1..24 | ForEach-Object { "page-{0:D2}.png" -f $_ })
    if (Compare-Object $ExpectedQetPages $QetPages) { throw 'QET baseline PDF render set is not exactly pages 01 through 24' }
    Invoke-Native $Python 'scripts\build_pdf_contact_sheets.py'

    Invoke-Native $Python 'scripts\validate_project.py'
    Assert-CleanGitState
    Invoke-Native $Python 'scripts\verify_manifest.py' '--source' 'head' '--require-clean'
    Write-Output "reproduction_result=PASS source=HEAD workbook_sha256=$WorkbookHash2 pdf_sha256=$PdfHash2"
}
finally { Pop-Location }
