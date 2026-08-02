$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RuntimeRoot = 'C:\Users\chand\.cache\codex-runtimes\codex-primary-runtime\dependencies'
$Python = Join-Path $RuntimeRoot 'python\python.exe'
$Node = Join-Path $RuntimeRoot 'node\bin\node.exe'
$NodeModules = Join-Path $RuntimeRoot 'node\node_modules'
$Poppler = Join-Path $RuntimeRoot 'native\poppler\Library\bin'
$BuildJunction = Join-Path $ProjectRoot 'node_modules'

Push-Location $ProjectRoot
try {
    & $Python 'scripts\build_project.py'
    & $Python -m unittest discover -s '11_simulation\tests' -v
    & $Python '11_simulation\run_scenarios.py'
    Push-Location '07_nvidia_vision'
    try { & $Python -m unittest -v 'test_plc_interface_harness.py' } finally { Pop-Location }

    if (-not (Test-Path -LiteralPath $BuildJunction)) {
        New-Item -ItemType Junction -Path $BuildJunction -Target $NodeModules | Out-Null
    }
    try { & $Node 'scripts\build_workbook.mjs' }
    finally {
        $Item = Get-Item -LiteralPath $BuildJunction -Force
        if ($Item.LinkType -eq 'Junction' -and $Item.Target -contains $NodeModules) {
            [System.IO.Directory]::Delete($BuildJunction, $false)
        }
    }
    & $Python 'scripts\build_contact_sheets.py'
    & $Python 'scripts\build_release_pdf.py'
    New-Item -ItemType Directory -Force -Path '14_qa\pdf_renders\release' | Out-Null
    & (Join-Path $Poppler 'pdftoppm.exe') -png -r 120 'release\FC01_release_evidence.pdf' '14_qa\pdf_renders\release\page'
    & $Python 'scripts\build_pdf_contact_sheets.py'
    & $Python 'scripts\validate_project.py'
}
finally { Pop-Location }
