#!/bin/bash
# This script sets up the required certificates for securing helm/tiller with TLS
# See https://github.com/kubernetes/helm/blob/master/docs/tiller_ssl.md

on_error() {
    echo "Error at $(caller), aborting"
    popd
    exit 1
}
trap on_error ERR

export OUTPUT_DIR="${1// }"
if [[ -z $OUTPUT_DIR ]]; then
  echo "Need to provide OUTPUT_DIR as argument"
  exit 2
fi

echo "Script to generate Certifate Authority (CA) and certificates"
echo "to secure both helm and tiller with TLS"
echo ""
echo "Requires openssl to be installed"
echo ""
echo "*** Generate CA key"

CERT_SUBJ="/C=GB/ST=Internet/L=Server/O=Helm TLS Org/CN=example.com"
openssl genrsa -out $OUTPUT_DIR/ca.key.pem 4096
echo ""
echo "*** Generate CA"
openssl req -key $OUTPUT_DIR/ca.key.pem -new -x509 -days 7300 -sha256 -out $OUTPUT_DIR/ca.cert.pem -extensions v3_ca -subj "$CERT_SUBJ"

echo ""
echo "*** Generate tiller client key"
openssl genrsa -out $OUTPUT_DIR/tiller.key.pem 4096
echo ""
echo "*** Generate helm client key"
openssl genrsa -out $OUTPUT_DIR/helm.key.pem 4096

echo ""
echo "*** Generate Tiller CSR"
openssl req -key $OUTPUT_DIR/tiller.key.pem -new -sha256 -out $OUTPUT_DIR/tiller.csr.pem -subj "$CERT_SUBJ"

echo ""
echo "*** Generate Helm CSR"
openssl req -key $OUTPUT_DIR/helm.key.pem -new -sha256 -out $OUTPUT_DIR/helm.csr.pem -subj "$CERT_SUBJ"

echo "*** Sign tiller CSR with CA certificate"
openssl x509 -req -CA $OUTPUT_DIR/ca.cert.pem -CAkey $OUTPUT_DIR/ca.key.pem -CAcreateserial -in $OUTPUT_DIR/tiller.csr.pem -out $OUTPUT_DIR/tiller.cert.pem -days 365

echo ""
echo "*** Sign helm CSR with CA certificate"
openssl x509 -req -CA $OUTPUT_DIR/ca.cert.pem -CAkey $OUTPUT_DIR/ca.key.pem -CAcreateserial -in $OUTPUT_DIR/helm.csr.pem -out $OUTPUT_DIR/helm.cert.pem -days 365
