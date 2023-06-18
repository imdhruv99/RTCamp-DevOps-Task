import subprocess
import platform
from pyuac import main_requires_admin

from logger import Logger

logger = Logger()


class DockerManager:
    """
    Class for managing Docker dependencies and operations.
    """

    @staticmethod
    def check_dependency_installed(dependency):
        """
        Checks if a dependency is installed.

        This method checks if the specified dependency is installed by running the command with the '--version'
        argument. It returns True if the dependency is found, and False otherwise.

        :param dependency: The name of the dependency.
        :return: True if the dependency is installed, False otherwise.
        """

        try:
            subprocess.run([dependency, '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except FileNotFoundError:
            return False
        return True

    @staticmethod
    def install_dependency(dependency):
        """
        Installs a dependency.

        This method installs the specified dependency based on the operating system. It uses platform-specific commands
        to install the dependency.

        :param dependency: The name of the dependency.
        :return: None
        """

        logger.info(f"{dependency} is not installed. Installing...")
        if platform.system() == 'Linux':
            distro = platform.linux_distribution()
            if distro[0].lower() in ['rhel', 'centos', 'suse']:
                subprocess.run(['sudo', 'yum', 'install', '-y', dependency], check=True)
            elif distro[0].lower() == 'ubuntu':
                subprocess.run(['sudo', 'apt', 'install', '-y', dependency], check=True)
            else:
                logger.info("Package installation is not supported on this Linux distribution.")
        elif platform.system() == 'Darwin':
            subprocess.run(['brew', 'install', dependency], check=True)
        elif platform.system() == 'Windows':
            subprocess.run(['choco', 'install', '-y', dependency], check=True)
        else:
            logger.info("Package installation is not supported on this operating system.")

    @staticmethod
    @main_requires_admin
    def create_symbolic_link(source, target):
        """
        Creates a symbolic link.

        This method creates a symbolic link from the source path to the target path. The appropriate command is executed
        based on the operating system.

        :param source: The path of the source file or directory.
        :param target: The path of the target location for the symbolic link.
        :return: None
        """
        
        if platform.system() == 'Linux':
            subprocess.run(['sudo', 'ln', '-s', source, target], check=True)
        elif platform.system() == 'Windows':
            command = ['cmd', '/C', 'mklink', '/D', target, source]
            subprocess.run(command, check=True)
        else:
            logger.info("Symbolic link creation is not supported on this operating system.")
