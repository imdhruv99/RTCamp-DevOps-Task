import os
import subprocess
import sys
import platform
from pyuac import main_requires_admin

def check_dependency_installed(dependency):
    try:
        subprocess.run([dependency, '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except FileNotFoundError:
        return False
    return True

def install_dependency(dependency):
    print(f"{dependency} is not installed. Installing...")

    if platform.system() == 'Linux':
        subprocess.run(['sudo', 'apt', 'install', '-y', dependency], check=True)
    elif platform.system() == 'Windows':
        # Handle Windows package installation, e.g., using Chocolatey or other package managers
        print("Package installation is not supported on Windows in this script.")
    else:
        print("Package installation is not supported on this operating system.")

@main_requires_admin
def create_symbolic_link(source, target):
    if platform.system() == 'Linux':
        subprocess.run(['sudo', 'ln', '-s', source, target], check=True)
    elif platform.system() == 'Windows':
        command = ['cmd', '/C', 'mklink', '/D', target, source]
        subprocess.run(command, check=True)
    else:
        print("Symbolic link creation is not supported on this operating system.")

def create_wordpress_site(site_name):
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

    create_symbolic_link(nginx_conf_path, nginx_conf_symlink)

    # Start containers
    subprocess.run(['docker-compose', 'up', '-d'], check=True)

def enable_disable_site(action):
    if action == 'enable':
        subprocess.run(['docker-compose', 'start'], check=True)
        print("Site enabled.")
    elif action == 'disable':
        subprocess.run(['docker-compose', 'stop'], check=True)
        print("Site disabled.")

def delete_site(site_name):
    os.chdir(site_name)
    subprocess.run(['docker-compose', 'down'], check=True)
    os.chdir('..')
    subprocess.run(['sudo', 'rm', '-rf', site_name])
    print("Site deleted.")

@main_requires_admin
def add_hosts_entry(site_name):
    if platform.system() == 'Windows':
        # Windows hosts file location
        hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
    elif platform.system() == 'Linux':
        # Linux hosts file location
        hosts_path = '/etc/hosts'
    else:
        print("Hosts file modification is not supported on this operating system.")
        return

    try:
        with open(hosts_path, 'a') as hosts_file:
            hosts_file.write(f'127.0.0.1 {site_name}\n')
        print("Hosts entry added successfully.")
    except Exception as e:
        print(f"Failed to add hosts entry: {str(e)}")

def main():
    if not check_dependency_installed('docker'):
        install_dependency('docker')

    if not check_dependency_installed('docker-compose'):
        install_dependency('docker-compose')

    if len(sys.argv) < 2:
        print("Please provide a site name as a command-line argument.")
        sys.exit(1)

    site_name = sys.argv[1]

    if not os.path.exists(site_name):
        os.makedirs(site_name)

    create_wordpress_site(site_name)

    # Add /etc/hosts entry
    add_hosts_entry(site_name)

    print("WordPress site created successfully.")

    while True:
        action = input("Enter 'open' to open the site in a browser, 'enable' to enable the site, 'disable' to disable the site, 'delete' to delete the site, or 'exit' to quit: ")
        
        if action == 'open':
            subprocess.run(['xdg-open', f'http://{site_name}'])
        elif action in ['enable', 'disable']:
            enable_disable_site(action)
        elif action == 'delete':
            delete_site(site_name)
            break
        elif action == 'exit':
            break
        else:
            print("Invalid action.")

if __name__ == '__main__':
    main()
