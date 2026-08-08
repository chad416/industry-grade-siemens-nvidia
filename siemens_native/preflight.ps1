$ErrorActionPreference = 'Stop'
$portal = 'C:\Program Files\Siemens\Automation\Portal V20\Bin\Siemens.Automation.Portal.exe'
$openness = 'C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20\Siemens.Engineering.dll'
$alm = 'C:\Program Files\Siemens\Automation\Automation License Manager\almapp\almapp64x.exe'
$groups = whoami /groups | Out-String
$result = [ordered]@{
  captured_utc = [DateTime]::UtcNow.ToString('o')
  identity = (whoami)
  portal_present = Test-Path -LiteralPath $portal
  portal_version = if (Test-Path -LiteralPath $portal) { (Get-Item $portal).VersionInfo.FileVersion } else { $null }
  openness_present = Test-Path -LiteralPath $openness
  openness_group = $groups -match 'Siemens TIA Openness'
  alm_present = Test-Path -LiteralPath $alm
  startdrive_present = [bool](Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object DisplayName -Match 'Startdrive')
  plcsim_present = [bool](Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object DisplayName -Match 'PLCSIM')
  licence_entitlement = 'MUST BE VERIFIED INTERACTIVELY IN ALM; KEYS MUST NOT BE EXPORTED'
}
$result | ConvertTo-Json -Depth 3
if (-not $result.portal_present -or -not $result.openness_present -or -not $result.openness_group) { exit 2 }
