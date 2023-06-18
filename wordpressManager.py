import os
import subprocess
import platform
from pyuac import main_requires_admin

from dockerManager import DockerManager
from logger import Logger

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
            Logger.info("Site enabled.")
        elif action == 'disable':
            subprocess.run(['docker-compose', 'stop'], check=True)
            Logger.info("Site disabled.")

    @staticmethod
    def delete_site(site_name):
        """
        Deletes a WordPress site.

        This method stops and removes the Docker containers associated with the WordPress site. It also deletes the
        site's directory.

        :param site_name: The name of the WordPress site.
        :return: None
        """

        os.chdir(site_name)
        subprocess.run(['docker-compose', 'down'], check=True)
        os.chdir('..')
        subprocess.run(['sudo', 'rm', '-rf', site_name])
        Logger.info("Site deleted.")

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
            Logger.info("Hosts file modification is not supported on this operating system.")
            return

        try:
            with open(hosts_path, 'a') as hosts_file:
                hosts_file.write(f'127.0.0.1 {site_name}\n')
            Logger.info("Hosts entry added successfully.")
        except Exception as e:
            Logger.error(f"Failed to add hosts entry: {str(e)}")
