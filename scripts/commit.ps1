param (
    [Parameter(Mandatory = $true)][ValidateSet('feat','fix','chore','docs','refactor','test','ci','perf')]$Type,
    [string]$Scope,
    [Parameter(Mandatory = $true)][string]$Summary
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path "$scriptDir\.."
Set-Location $repoRoot

$message = if ([string]::IsNullOrWhiteSpace($Scope)) {"$Type: $Summary"} else {"$Type($Scope): $Summary"}

Write-Host "[$Type] executando testes antes do commit..."
$env:SECRET_KEY = 'test-secret'
$testResult = & python -m pytest -q tests
if ($LASTEXITCODE -ne 0) {
    Write-Error "Testes falharam; abortando commit."
    exit $LASTEXITCODE
}

Write-Host "Testes OK. Preparando commit com mensagem: $message"
git status -sb
git add -A
git commit -m $message
