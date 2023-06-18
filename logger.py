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
