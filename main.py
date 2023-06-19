import os
import pathlib
import shutil
import subprocess
import sys
import platform
from pyuac import main_requires_admin
import argparse
import logging

class Logger:
    """
    Custom logger class for handling logging in the WordPress site management script.
    """
    def __init__(self):
        """
        Initializes a Logger instance.

        The logger is set to log messages at the INFO level by default. It logs messages to the console
        and uses a specific log message format.

        :return: None
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.stream_handler = logging.StreamHandler()
        self.stream_handler.setLevel(logging.INFO)
        self.stream_handler.setFormatter(formatter)
        self.logger.addHandler(self.stream_handler)

    def info(self, message):
        """
        Logs an informational message.

        :param message: The message to log.
        :return: None
        """
        self.logger.info(message)

    def error(self, message):
        """
        Logs an error message.

        :param message: The error message to log.
        :return: None
        """
        self.logger.error(message)

    def set_level(self, level):
        """
        Sets the logging level for the logger and stream handler.

        :param level: The logging level to set (e.g., logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR).
        :return: None
        """
        self.logger.setLevel(level)
        self.stream_handler.setLevel(level)


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


class WordPressManager:
    """
    Class for managing WordPress sites using Docker and NGINX.
    """
    @staticmethod
    def create_wordpress_site(site_name):
        """
        Creates a new WordPress site using Docker and NGINX.

        This method creates a Docker Compose file with the necessary configurations for running a WordPress site
        and an NGINX configuration file for routing traffic to the WordPress container. It also creates a symbolic
        link to the NGINX configuration file and starts the containers.

        :param site_name: The name of the WordPress site.
        :return: None
        """

        os.chdir(site_name)

        # Create Docker Compose file
        compose_content = f'''version: '3'
services:
  db:
    image: mysql:latest
    restart: always
    environment:
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wordpress
      MYSQL_PASSWORD: wordpress
      MYSQL_RANDOM_ROOT_PASSWORD: '1'
    volumes:
      - db_data:/var/lib/mysql
  wordpress:
    depends_on:
      - db
    image: wordpress:latest
    restart: always
    environment:
      WORDPRESS_DB_HOST: db:3306
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress
    ports:
      - "80:80"
    volumes:
      - ./wp-content:/var/www/html/wp-content
volumes:
  db_data:
'''
        with open('docker-compose.yml', 'w') as compose_file:
            compose_file.write(compose_content)

        # Create NGINX config file
        nginx_content = f'''server {{
    listen 80;
    server_name {site_name};

    location / {{
        proxy_pass http://wordpress:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
'''
        with open('nginx.conf', 'w') as nginx_file:
            nginx_file.write(nginx_content)

        nginx_conf_path = os.path.abspath('nginx.conf')
        if platform.system() == 'Linux':
            nginx_conf_symlink = '/etc/nginx/sites-enabled/'
        elif platform.system() == 'Windows':
            nginx_conf_symlink = os.path.join('C:\\nginx\\conf\\sites-enabled\\', site_name)

        DockerManager.create_symbolic_link(nginx_conf_path, nginx_conf_symlink)

        # Start containers
        subprocess.run(['docker-compose', 'up', '-d'], check=True)

    @staticmethod
    def enable_disable_site(action):
        """
        Enables or disables a WordPress site.

        This method starts or stops the Docker containers associated with the WordPress site based on the provided
        action ('enable' or 'disable').

        :param action: The action to perform ('enable' or 'disable').
        :return: None
        """
        if action == 'enable':
            subprocess.run(['docker-compose', 'start'], check=True)
            logger.info("Site enabled.")
        elif action == 'disable':
            subprocess.run(['docker-compose', 'stop'], check=True)
            logger.info("Site disabled.")

    @staticmethod
    def delete_site(site_name):
        """
        Deletes a WordPress site.

        This method stops and removes the Docker containers associated with the WordPress site. It also deletes the
        site's directory.

        :param site_name: The name of the WordPress site.
        :return: None
        """
        site_path = pathlib.Path(site_name).resolve()
        os.chdir(site_path.parent)
        subprocess.run(['docker-compose', 'down'], check=True)
        os.chdir('..')
        site_path = os.path.abspath(site_name).replace('\\', '/')
        shutil.rmtree(site_path)
        logger.info("Site deleted.")

    @staticmethod
    @main_requires_admin
    def add_hosts_entry(site_name):
        """
        Adds a hosts file entry for the WordPress site.

        This method adds an entry to the hosts file to map the site's domain name to the loopback address (127.0.0.1).
        The hosts file is located at different paths depending on the operating system.

        :param site_name: The name of the WordPress site.
        :return: None
        """
        if platform.system() == 'Windows':
            # Windows hosts file location
            hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
        elif platform.system() == 'Linux':
            # Linux hosts file location
            hosts_path = '/etc/hosts'
        else:
            logger.info("Hosts file modification is not supported on this operating system.")
            return

        try:
            with open(hosts_path, 'a') as hosts_file:
                hosts_file.write(f'127.0.0.1 {site_name}\n')
            logger.info("Hosts entry added successfully.")
        except Exception as e:
            logger.error(f"Failed to add hosts entry: {str(e)}")


def main():
    """
    Main method to execute the WordPress site management script.

    It checks the dependencies, creates a WordPress site, adds a hosts entry, and performs actions based on
    command-line arguments.

    :return: None
    """
    if not DockerManager.check_dependency_installed('docker'):
        DockerManager.install_dependency('docker')

    if not DockerManager.check_dependency_installed('docker-compose'):
        DockerManager.install_dependency('docker-compose')

    if len(sys.argv) < 2:
        logger.error("Please provide a site name as a command-line argument.")
        sys.exit(1)

    site_name = sys.argv[1]

    if not os.path.exists(site_name):
        os.makedirs(site_name)

    WordPressManager.create_wordpress_site(site_name)

    # Add /etc/hosts entry
    WordPressManager.add_hosts_entry(site_name)

    logger.info("WordPress site created successfully.")

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='WordPress site management script')

    # Add a positional argument for the site name
    parser.add_argument('site_name', help='Name of the WordPress site')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')
    enable_parser = subparsers.add_parser('enable', help='Enable the site')
    disable_parser = subparsers.add_parser('disable', help='Disable the site')
    delete_parser = subparsers.add_parser('delete', help='Delete the site')

    # Parse the command-line arguments
    args = parser.parse_args()

    site_name = args.site_name

    if args.action == 'enable':
        WordPressManager.enable_disable_site('enable')
    elif args.action == 'disable':
        WordPressManager.enable_disable_site('disable')
    elif args.action == 'delete':
        WordPressManager.delete_site(site_name)
    elif args.action is None:
        logger.info("Your site is running on localhost.")
    else:
        logger.info("Invalid action.")


if __name__ == '__main__':
    logger = Logger()
    main()
