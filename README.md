# Summary
When accessing a single kubernetes cluster, or multiple kubernetes clusters all with the same TLS files installed, it it relatively easy to secure `helm` with TLS.

The recommended approach is to copy the TLS files to your `$HELM_HOME` directory, and then you can access `helm` with:
```
helm --tls  [...commands...]
```

For more details about this, see for example https://medium.com/google-cloud/install-secure-helm-in-gke-254d520061f7.


### The problem
However, managing helm certificates for secure TLS communication to multiple kubernetes clusters is tricky, requiring 
careful creation and management of certificates.

The challenge here is described by Maor Friedman at https://medium.com/nuvo-group-tech/configure-helm-tls-communication-with-multiple-kubernetes-clusters-5e58674352e2.

# Aim of this project
Pending the arrival of helm 3.x (see [here](https://sweetcode.io/a-first-look-at-the-helm-3-plan/)), this project provides some automation in the creation and management of multiple sets of helm TLS certificates and applying them into your cluster. 

It also provides a script wrapper that allows the following command-line:
```
helm --tls --tiller-namespace="$TILLER_NAMESPACE" \
  --tls-ca-cert="$HELM_CA_CERT_PEM" --tls-cert="$HELM_CERT_PEM" \
  --tls-key="$HELM_KEY_PEM" [...commands...]
```

to reduce to:

```
helmt  [...commands...]
```
# Configuration
## Pre-requisites
The scripts are cross-platform, tested on Ubuntu 18.04 and Windows 10. They should work with minimal updates required on other platforms.

For basic use you will need at least:
- Python 3.x (3.6 or higher preferred)
- The `helm` binary for your platform (tested on 2.11). This includes all pre-requisites for helm, such as `kubectl`
- bash shell on Linux / Mac OS X.
  
  or 

  powershell on Windows.

For generating certificates you also need `openssl` library.

## Configuring a helm client to communicate with a k8s cluster

### 1. Installing the helm certs locally
Find the `[environment name]-helm-client.tar.xz` generated from the "Installing Helm on a cluster" section of this documentation. Your cluster administrator should be able to provide it.

To install the certs locally into your `$HELM_HOME` folder do:
`python3 helm_env.py install yourfile-helm-client.tar.xz`

To check these have installed and to see what environments you have available type:
`python3 helm_env.py list`

Assuming the relevant secrets are in .tls folder you can run `source helm-client-config.sh` to copy the certificates into your `~/.helm` directory, 
this also sets the correct environment variables.

### 2. Using the `helmt` wrapper

#### bash setup
In a bash shell, you configure the `helmt` wrapper by:

`source ./sh_helmt.sh [environment name]`

#### powershell setup
In a Powershell terminal, you configure the `helmt` wrapper by:

`. .\ps1_helmt.ps1 [environment name]`

#### Testing the link
To test the helmt wrapper type  ```helmt ls --debug```, even if you have no helm charts
installed in the cluster.
This will connect to your cluster, providing debug output about how the link is secured between helm and tiller.

You expect to see something like the following, with no errors about TLS.
```
 > helmt ls --debug
[debug] Created tunnel using local port: '57546'

[debug] SERVER: "127.0.0.1:57546"

[debug] Host="", Key=".../helm.key.pem", Cert=".../helm.cert.pem", CA=".../ca.cert.pem"
```
#### Integrating with other scripts
The helmt wrappers set the following environment variables you can use in other scripts to automate installs.
  - `TILLER_NAMESPACE` - namespace tiller is installed in
  - `HELM_CA_CERT_PEM` - CA certificate
  - `HELM_CERT_PEM` - Helm certificate
  - `HELM_KEY_PEM` - Helm private key

This allows you to rebuild the full `helm` command line without requiring any user interaction, for example:
```
helm --tls --tiller-namespace="$TILLER_NAMESPACE" \
  --tls-ca-cert="$HELM_CA_CERT_PEM" --tls-cert="$HELM_CERT_PEM" \
  --tls-key="$HELM_KEY_PEM" ls
```
# Admistration
## Initializing Helm on a cluster you manage
### Pre-requisites
Firstly you need to set up any RBAC, including namespaces and service accounts. This is specific to your requirements. Only assumption is that the service account you will use will be in the namespace that you install tiller to.

### Generating the TLS certs and keys
Once that is configured, you will need to generate some TLS certificates and keys that helm and tiller will use.
This requires openssl to be installed (tested on Ubuntu 18.04 LTS and Windows Subsystem for Linux with Ubuntu 18.04). 

`python3 helm_admin.py cert-gen [environment name] [namespace]`

This will generate all the required certificates in the .tls directory, and 3 archives.
1) `[environment name]-helm-client.tar.xz` All the files you need locally to authenticate the helm client against the tiller install in k8s. This should be distributed to everyone who needs helm access to install software.
1) `[environment name]-tiller-server.tar.xz` All the files you need locally to install or reinstall the tiller server against the tiller install in k8s. This should be distributed to cluster admins who need to reinstall tiller in case of a problem with the existing install.
1) `[environment name]-all.tar.xz` All the generated files, including the CA key. This is enough information to be able to generate more certificates so should be secured if you need it for future reference.

### Installing helm into a cluster
Checklist:
- You have RBAC setup correctly and service accounts etc ready.
- You have some TLS certs generated and access to the `-tiller-server.tar.xz` file.

`python3 helm_admin.py install [environment]-tiller-server.tar.xz [name of service account]`

