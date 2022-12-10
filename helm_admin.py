import argparse
import subprocess
import platform
import os
from pathlib import Path
import shutil
import tarfile

SCRIPT_PATH = Path(os.path.dirname(os.path.realpath(__file__)))


# convenience error class
class HelmError(Exception):
    pass


def run_command(command_list, check=True):
    print(command_list)
    subprocess.run(command_list, check=check)


def clear_cert_path():
    cert_path = SCRIPT_PATH / ".tls"
    if cert_path.exists():
        shutil.rmtree(str(cert_path))
    cert_path.mkdir()
    return cert_path


def certificate_generate(certs_name, tiller_namespace):
    cert_path = clear_cert_path()
    resources_path = SCRIPT_PATH / "resources"

    script_file = resources_path / "helm-cert-gen.sh"
    subprocess.run([str(script_file), str(cert_path)])
    namespace_path = cert_path / "namespace.txt"
    with namespace_path.open("w") as file_handle:
        print(tiller_namespace, file=file_handle)

    tar_all = cert_path / "{}-all.tar.xz".format(certs_name)
    with tarfile.open(tar_all, "x:xz") as tar:
        print("Tar'ing all files to {}".format(tar_all))
        tar.add(cert_path, arcname=certs_name)

    tar_tiller = cert_path / "{}-tiller-server.tar.xz".format(certs_name)
    with tarfile.open(tar_tiller, "x:xz") as tar:
        print("Tar'ing tiller (server) files to {}".format(tar_tiller))
        tar.add(cert_path / "ca.cert.pem", arcname=certs_name + "/ca.cert.pem")
        tar.add(cert_path / "tiller.key.pem", arcname=certs_name + "/tiller.key.pem")
        tar.add(cert_path / "tiller.cert.pem", arcname=certs_name + "/tiller.cert.pem")
        tar.add(namespace_path, arcname=certs_name + "/namespace.txt")

    tar_helm = cert_path / "{}-helm-client.tar.xz".format(certs_name)
    with tarfile.open(tar_helm, "x:xz") as tar:
        print("Tar'ing helm (client) files to {}".format(tar_helm))
        tar.add(cert_path / "ca.cert.pem", arcname=certs_name + "/ca.cert.pem")
        tar.add(cert_path / "helm.key.pem", arcname=certs_name + "/helm.key.pem")
        tar.add(cert_path / "helm.cert.pem", arcname=certs_name + "/helm.cert.pem")
        tar.add(namespace_path, arcname=certs_name + "/namespace.txt")


def helm_untar(archive_file, required_files):
    cert_path = clear_cert_path()
    with tarfile.open(archive_file, "r") as tar:
        print("Un tar'ing data from {}".format(archive_file))
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, path=cert_path)

    cert_subdir = None
    for ii in cert_path.iterdir():
        if ii.is_dir():
            cert_subdir = ii

    if cert_subdir is None:
        raise HelmError("Invalid archive missing directory")

    for ff in required_files:
        if not (cert_subdir / ff).exists():
            raise HelmError("Missing expected file {}".format(ff))

    namespace_file = cert_subdir / "namespace.txt"
    with namespace_file.open("r") as file_handle:
        tiller_namespace = file_handle.readline().strip()
    return cert_subdir, tiller_namespace


def helm_init(archive_file, service_account):
    cert_subdir, tiller_namespace = helm_untar(archive_file,
                             ["ca.cert.pem", "tiller.key.pem", "tiller.cert.pem", "namespace.txt"])

    cmd = [
        "helm", "init", "--service-account={}".format(service_account), "--upgrade",
        "--tiller-namespace={}".format(tiller_namespace),
        "--tiller-tls", "--tiller-tls-cert={}".format(cert_subdir / "tiller.cert.pem"),
        "--tiller-tls-key={}".format(cert_subdir / "tiller.key.pem"),
        "--tiller-tls-verify",
        "--tls-ca-cert={}".format(cert_subdir / "ca.cert.pem")
    ]
    run_command(cmd)


def helm_remove(archive_file):
    cert_subdir, tiller_namespace = helm_untar(archive_file,
                             ["ca.cert.pem", "helm.key.pem", "helm.cert.pem", "namespace.txt"])

    cmd = [
        "helm", "reset", "--tiller-namespace={}".format(tiller_namespace), "--tls", "--tls-cert={}".format(
            cert_subdir / "helm.cert.pem"), "--tls-key={}".format(cert_subdir / "helm.key.pem"),
        "--tls", "--tls-ca-cert={}".format(
            cert_subdir / "ca.cert.pem")
    ]
    run_command(cmd)
    print(" ")
    print("*** Helm's tiller has been removed")
    print("***   - check that 'kubectl get po -n [TILLER_NAMESPACE]' shows no pods")
    print("***     you might have to manually delete it")


def main(args, parser):
    command = args.command
    print("Will perform '{}' operation for helm".format(command))

    if command == "cert-gen":
        certificate_generate(args.certs_name, args.tiller_namespace)
    elif command == "install":
        helm_init(args.archive_file, args.service_account)
    elif command == "remove":
        helm_remove(args.archive_file)
    else:
        print("! Invalid command {} !".format(command))
        parser.print_help()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Helm -> k8s TLS environment management scripts')

    subparsers = parser.add_subparsers(help="sub-command help", dest="command")

    certgen_parser = subparsers.add_parser(
        "cert-gen", help="Generate certificates (probably needs Linux/WSL)")
    certgen_parser.add_argument(
        "certs_name",
        help="Name of the certificate group, e.g. Dev_201811_1. Will be used in the tar.xz files")
    certgen_parser.add_argument("tiller_namespace", help="Name of the tiller namespace")

    install_parser = subparsers.add_parser(
        "install", help="Install helm from k8s cluster (that kubectl uses)")
    install_parser.add_argument(
        "archive_file", help="Previously generated *tiller-server* TLS certs archive")
    install_parser.add_argument("service_account", help="Name of the tiller service account")

    remove_parser = subparsers.add_parser(
        "remove", help="Remove helm from k8s cluster (that kubectl uses)")
    remove_parser.add_argument(
        "archive_file", help="Previously generated *helm-client* TLS certs archive")

    args = parser.parse_args()
    main(args, parser)
