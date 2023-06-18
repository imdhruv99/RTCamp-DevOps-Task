import subprocess
import platform
from pyuac import main_requires_admin

from logger import Logger


class DockerManager:
    @staticmethod
    def check_dependency_installed(dependency):
        try:
            subprocess.run([dependency, '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except FileNotFoundError:
            return False
        return True

    @staticmethod
    def install_dependency(dependency):
        Logger.info(f"{dependency} is not installed. Installing...")
        if platform.system() == 'Linux':
            distro = platform.linux_distribution()
            if distro[0].lower() in ['rhel', 'centos', 'suse']:
                subprocess.run(['sudo', 'yum', 'install', '-y', dependency], check=True)
            elif distro[0].lower() == 'ubuntu':
                subprocess.run(['sudo', 'apt', 'install', '-y', dependency], check=True)
            else:
                Logger.info("Package installation is not supported on this Linux distribution.")
        elif platform.system() == 'Darwin':
            subprocess.run(['brew', 'install', dependency], check=True)
        elif platform.system() == 'Windows':
            subprocess.run(['choco', 'install', '-y', dependency], check=True)
        else:
            Logger.info("Package installation is not supported on this operating system.")

    @staticmethod
    @main_requires_admin
    def create_symbolic_link(source, target):
        if platform.system() == 'Linux':
            subprocess.run(['sudo', 'ln', '-s', source, target], check=True)
        elif platform.system() == 'Windows':
            command = ['cmd', '/C', 'mklink', '/D', target, source]
            subprocess.run(command, check=True)
        else:
            Logger.info("Symbolic link creation is not supported on this operating system.")
