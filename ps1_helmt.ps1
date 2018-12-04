param (
  [Parameter(Mandatory = $true)][String] $helmEnvironment
)
$ErrorActionPreference = "Stop"

function global:helmt {
  Param(
    [parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Passthrough
  )

  & helm --tls --tiller-namespace="$env:TILLER_NAMESPACE" `
  --tls-ca-cert="$env:HELM_CA_CERT_PEM" --tls-cert="$env:HELM_CERT_PEM" `
  --tls-key="$env:HELM_KEY_PEM" @Passthrough 
}

function helpAndThrow([string] $errorMessage) {
  Write-Host @"
usage: . ps1_helm.ps1 [name of environment]

  This script needs to be "." sourced.
  Setup helm environment.
  Use python helm_env.py to list available environments.

"@
  
  throw $errorMessage
}

# script must  always be sourced 
$isDotSourced = $MyInvocation.InvocationName -eq '.' -or $MyInvocation.Line -eq ''
if (-not $isDotSourced) {
  helpAndThrow "This script should be dot sourced (invoked with .) as it saves variables to current PS session"
}

#if ($helmEnvironment.Length 
if (-not (Test-Path env:HELM_HOME)) {
  $helmHome="$env:HOME\.helm"
} else {
  $helmHome="$env:HELM_HOME"
}

$helmTlsRoot="$helmHome\tls\$HelmEnvironment"
if (-not (Test-Path $helmTlsRoot)) {
  helpAndThrow ("Aborting: {0} does not exist" -f $helmTlsRoot)
} 
$env:HELM_HOME=$helmHome
$env:HELM_ENVIRONMENT=$HelmEnvironment
$env:TILLER_NAMESPACE=Get-Content "$helmTlsRoot\namespace.txt"
$env:HELM_CA_CERT_PEM="$helmTlsRoot\ca.cert.pem"
$env:HELM_CERT_PEM="$helmTlsRoot\helm.cert.pem"
$env:HELM_KEY_PEM="$helmTlsRoot\helm.key.pem"
  
Write-Host "Helm configured to use $env:HELM_ENVIRONMENT's TLS certs"
Write-Host "via 'helmt [command]'"

