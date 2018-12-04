import argparse
import os
from pathlib import Path
import shutil
import tarfile
import tempfile

SCRIPT_PATH = Path(os.path.dirname(os.path.realpath(__file__)))


# convenience error class
class HelmError(Exception):
    pass


def helm_list(helm_home_tls):
    if helm_home_tls.exists():
        environments = []
        for ii in helm_home_tls.iterdir():
            if ii.is_dir():
                environments.append(ii.name)
        if environments:                
            print("Environments:")
            for ee in environments:
                print("  " + ee)
        else:
            print("No environments available")    
    else:
        print("No environments available")


def helm_install(helm_home_tls, archive_file):
    required_files = ["ca.cert.pem", "helm.key.pem", "helm.cert.pem"]
    with tempfile.TemporaryDirectory() as tmpdir:
        with tarfile.open(archive_file, "r") as tar:
            print("Un tar'ing data from {}".format(archive_file))
            tar.extractall(path=tmpdir)
        tmpdir_path = Path(tmpdir)
        cert_subdir = None
        for ii in tmpdir_path.iterdir():
            if ii.is_dir():
                cert_subdir = ii

        if cert_subdir is None:
            raise HelmError("Invalid archive missing directory")

        for ff in required_files:
            if not (cert_subdir / ff).exists():
                raise HelmError("Missing expected file {}".format(ff))

        environment_name = cert_subdir.name
        print("*** Found environment '{}'".format(environment_name))

        helm_home_tls_dir = helm_home_tls / environment_name
        if helm_home_tls_dir.exists():
            print("Environment already exists, no need to install")
            return
        print("*** Copying files to {}".format(helm_home_tls_dir))

        shutil.copytree(cert_subdir, helm_home_tls_dir)


def helm_remove(helm_home_tls, environment_name):
    helm_home_tls_dir = helm_home_tls / environment_name
    if not helm_home_tls_dir.exists():
        print("Environment doesn't exist, no need to remove")
        return

    shutil.rmtree(helm_home_tls_dir)


def main(args, parser):
    command = args.command
    helm_home_tls = Path(os.path.expanduser("~/.helm/tls"))

    if command == "list":
        helm_list(helm_home_tls)
    elif command == "install":
        helm_install(helm_home_tls, args.archive_file)
    elif command == "remove":
        helm_remove(helm_home_tls, args.environment_name.strip())
    else:
        print("! Invalid command {} !".format(command))
        parser.print_help()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Helm configuration script')

    subparsers = parser.add_subparsers(help="sub-command help", dest="command")

    list_parser = subparsers.add_parser("list", help="List available environments")

    install_parser = subparsers.add_parser(
        "install",
        help="Install environment from previously generated *helm-client* TLS certs archive")
    install_parser.add_argument(
        "archive_file", help="Previously generated *helm-client* TLS certs archive")

    remove_parser = subparsers.add_parser("remove", help="Remove environment from local list")
    remove_parser.add_argument("environment_name", help="Name of environment")

    args = parser.parse_args()
    main(args, parser)
