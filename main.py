import argparse
import os
import sys

from dockerManager import DockerManager
from logger import Logger
from wordpressManager import WordPressManager

logger = Logger()


class Main:
    """
    Class representing the main entry point for the WordPress site management script.
    """

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
    main = Main.main()
