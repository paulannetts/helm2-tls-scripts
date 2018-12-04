#!/usr/bin/env bash 
#Use !/bin/bash -x  for debugging 

SCRIPT_NAME=$(basename $BASH_SOURCE)

function on_error() {
    echo "Error at $(caller), aborting"
    # don't exit, the trap will break, but set the return code
    RETURN=1
}

function help() {
    cat <<- EOF

usage: . $SCRIPT_NAME [name of environment]

This script needs to be "." sourced.
Setup helm environment.
Use python helm_env.py to list available environments.
EOF

    if [ -z "$1" ]; then
      return $1
    fi
}

# script will always be sourced - so break the loop on error
# set RETURN value

if [ "${BASH_SOURCE[0]}" == "${0}" ]
then
  echo "This script should be sourced, please try with 'source' or '.'"
  help
  exit -1
fi

export HELM_ENVIRONMENT="${1// }"
if [ -z "$HELM_ENVIRONMENT" ]; then
  echo "Need to provide HELM_ENVIRONMENT as argument"
  help -1
fi

RETURN=0
CONTINUE=true

function helmt() {
  helm --tls --tiller-namespace="$TILLER_NAMESPACE" \
  --tls-ca-cert="$HELM_CA_CERT_PEM" --tls-cert="$HELM_CERT_PEM" \
  --tls-key="$HELM_KEY_PEM" "$@"
}

while $CONTINUE; do
  CONTINUE=false
  trap 'on_error; break' ERR
  if [ -z "$HELM_HOME" ]; then
    export HELM_HOME="$HOME/.helm"
  fi

  if ! [ -d "$HELM_HOME/tls/$HELM_ENVIRONMENT" ]; then
    echo "*** ERROR ***"
    echo "Invalid environment - missing $HELM_HOME/tls/$HELM_ENVIRONMENT"
    return -1
  fi
  export TILLER_NAMESPACE=$(cat "$HELM_HOME/tls/$HELM_ENVIRONMENT/namespace.txt")
  export HELM_CA_CERT_PEM="$HELM_HOME/tls/$HELM_ENVIRONMENT/ca.cert.pem"
  export HELM_CERT_PEM="$HELM_HOME/tls/$HELM_ENVIRONMENT/helm.cert.pem"
  export HELM_KEY_PEM="$HELM_HOME/tls/$HELM_ENVIRONMENT/helm.key.pem"
  
  echo "Helm configured to use $HELM_ENVIRONMENT's TLS certs"
  echo "via 'helmt [command]'"
done
trap - ERR
CONTINUE=
DIRNAME=
return $RETURN;
