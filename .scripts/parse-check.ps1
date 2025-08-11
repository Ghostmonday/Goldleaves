$ErrorActionPreference = 'Stop'
$errors = $null
$text = Get-Content ..\merge-queue.ps1 -Raw
[void][System.Management.Automation.PSParser]::Tokenize($text, [ref]$errors)
if ($errors) {
  $errors | Select-Object Message, @{n='Line';e={$_.Extent.StartLineNumber}}, @{n='Col';e={$_.Extent.StartColumnNumber}}, @{n='Near';e={$_.Extent.Text}}
} else {
  Write-Host 'No parse errors.'
}
