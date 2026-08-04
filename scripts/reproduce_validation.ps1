param()

$ErrorActionPreference = 'Stop'
$env:PYTHONDONTWRITEBYTECODE = '1'
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

function Resolve-ExternalExecutable {
    param(
        [Parameter(Mandatory=$true)][string]$EnvironmentName,
        [Parameter(Mandatory=$true)][string]$KnownPath
    )
    $Explicit = [Environment]::GetEnvironmentVariable($EnvironmentName)
    $Candidate = if ($Explicit) { $Explicit } else { $KnownPath }
    if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
        throw "Unable to resolve $EnvironmentName; checked $Candidate"
    }
    return (Resolve-Path -LiteralPath $Candidate).Path
}

$Python = Resolve-Executable 'FC01_PYTHON' 'python\python.exe' @('python','python3')
$Node = Resolve-Executable 'FC01_NODE' 'node\bin\node.exe' @('node')
$NodeModules = Resolve-Directory 'FC01_NODE_MODULES' 'node\node_modules'
$Pdftoppm = Resolve-Executable 'FC01_PDFTOPPM' 'native\poppler\Library\bin\pdftoppm.exe' @('pdftoppm')
$OpcUaPython = Resolve-ExternalExecutable 'FC01_OPCUA_PYTHON' 'C:\Users\chand\AppData\Local\Temp\fc01-rev-e-opcua-venv\Scripts\python.exe'
$FreeCADCmd = Resolve-ExternalExecutable 'FC01_FREECADCMD' 'C:\Users\chand\.codex\visualizations\2026\08\01\019fbf33-0278-7863-9c85-46d6cc9a3115\fc\FreeCAD_1.1.3-Windows-x86_64-py311\bin\FreeCADCmd.exe'
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
    Invoke-Native $Python 'scripts\verify_qet_revision_e.py'
    if (Test-Path -LiteralPath 'scripts\verify_qet_revision_f.py') { Invoke-Native $Python 'scripts\verify_qet_revision_f.py' }
    Invoke-Native $Python '-m' 'unittest' 'discover' '-s' '11_simulation\tests' '-v'
    Invoke-Native $Python '11_simulation\run_scenarios.py'
    Invoke-Native $Python '11_simulation\run_vision_fault_scenarios.py'
    Invoke-Native $OpcUaPython '-m' 'unittest' 'discover' '-s' '07_nvidia_vision\edge_service\tests' '-v'
    Push-Location '07_nvidia_vision'
    try { Invoke-Native $Python '-m' 'unittest' '-v' 'test_plc_interface_harness.py' } finally { Pop-Location }
    Invoke-Native $FreeCADCmd 'scripts\verify_freecad_revision_e.py'
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

    Reset-GeneratedDirectory '14_qa\pdf_renders\release_f'
    Invoke-Native $Pdftoppm '-png' '-r' '140' 'release\FC01_release_evidence.pdf' '14_qa\pdf_renders\release_f\page'
    $ReleasePages = @(Get-ChildItem '14_qa\pdf_renders\release_f' -File | Sort-Object Name | ForEach-Object Name)
    $ExpectedReleasePages = @(1..6 | ForEach-Object { "page-$_.png" })
    if (Compare-Object $ExpectedReleasePages $ReleasePages) { throw 'Release PDF render set is not exactly pages 1 through 6' }

    Reset-GeneratedDirectory '14_qa\pdf_renders\qet_baseline'
    Invoke-Native $Pdftoppm '-png' '-r' '140' '03_electrical\native_baseline\filling_cell_schematics.pdf' '14_qa\pdf_renders\qet_baseline\page'
    $QetPages = @(Get-ChildItem '14_qa\pdf_renders\qet_baseline' -File | Sort-Object Name | ForEach-Object Name)
    $ExpectedQetPages = @(1..24 | ForEach-Object { "page-{0:D2}.png" -f $_ })
    if (Compare-Object $ExpectedQetPages $QetPages) { throw 'QET baseline PDF render set is not exactly pages 01 through 24' }

    Reset-GeneratedDirectory '14_qa\qet_revision_f_rendered'
    Invoke-Native $Pdftoppm '-png' '-r' '144' '03_electrical\revision_f_native_qet\FC01_revision_e_native_export.pdf' '14_qa\qet_revision_f_rendered\page'
    $QetRevisionFPages = @(Get-ChildItem '14_qa\qet_revision_f_rendered' -File | Sort-Object Name | ForEach-Object Name)
    $ExpectedQetRevisionFPages = @(1..26 | ForEach-Object { "page-{0:D2}.png" -f $_ })
    if (Compare-Object $ExpectedQetRevisionFPages $QetRevisionFPages) { throw 'Revision-F QET render set is not exactly pages 01 through 26' }
    Invoke-Native $Python 'scripts\verify_qet_revision_f.py'

    Reset-GeneratedDirectory '14_qa\pdf_renders\cad_general_arrangement'
    Invoke-Native $Pdftoppm '-png' '-r' '140' '09_panel_cad\revision_e\FC01_general_arrangement_revision_e.pdf' '14_qa\pdf_renders\cad_general_arrangement\page'
    $CadGaPages = @(Get-ChildItem '14_qa\pdf_renders\cad_general_arrangement' -File | Sort-Object Name | ForEach-Object Name)
    $ExpectedCadGaPages = @(1..4 | ForEach-Object { "page-$_.png" })
    if (Compare-Object $ExpectedCadGaPages $CadGaPages) { throw 'CAD general-arrangement render set is not exactly pages 1 through 4' }

    Reset-GeneratedDirectory '14_qa\pdf_renders\cad_mounting_plate'
    Invoke-Native $Pdftoppm '-png' '-r' '140' '09_panel_cad\revision_e\FC01_mounting_plate_dimensioned_revision_e.pdf' '14_qa\pdf_renders\cad_mounting_plate\page'
    $CadMpPages = @(Get-ChildItem '14_qa\pdf_renders\cad_mounting_plate' -File | Sort-Object Name | ForEach-Object Name)
    $ExpectedCadMpPages = @(1..2 | ForEach-Object { "page-$_.png" })
    if (Compare-Object $ExpectedCadMpPages $CadMpPages) { throw 'CAD mounting-plate render set is not exactly pages 1 through 2' }
    Invoke-Native $Python 'scripts\build_pdf_contact_sheets.py'

    Invoke-Native $Python 'scripts\validate_project.py'
    Invoke-Native $Python 'scripts\verify_revision_f.py'
    Assert-CleanGitState
    Invoke-Native $Python 'scripts\verify_manifest.py' '--source' 'head' '--require-clean'
    Write-Output "reproduction_result=PASS source=HEAD workbook_sha256=$WorkbookHash2 pdf_sha256=$PdfHash2"
}
finally { Pop-Location }
