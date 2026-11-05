param(
    [Parameter(Position=0)]
    [ValidateSet('login','prepare','run','verify','profile','session','events','calibrations','alarms','smoke','readings','inventory')]
    [string]$Command = 'verify',
    [string]$Email,
    [string]$RunFile
)
$ErrorActionPreference = 'Stop'
$runtimePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) {
    $runtimePython = (Get-Command python -ErrorAction Stop).Source
}
Push-Location $PSScriptRoot
try {
    if ($Command -eq 'login') {
        & $runtimePython -m src.auth
    } elseif ($Command -eq 'inventory') {
        & $runtimePython -m src.seeder inventory
    } else {
        $arguments = @('-m', 'src.qa_run', $Command)
        if ($Email) { $arguments += @('--email', $Email) }
        if ($RunFile) { $arguments += @('--run-file', $RunFile) }
        & $runtimePython @arguments
    }
    if ($LASTEXITCODE -ne 0) { throw "Seeder exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
