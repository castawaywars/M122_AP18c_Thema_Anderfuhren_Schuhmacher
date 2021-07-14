import logging
from ftplib import FTP
from configparser import ConfigParser

CONFIG_FILE_NAME: str = 'LB2_config.ini'
"""The name of the config file"""


def get_config() -> ConfigParser:
    """Get a ConfigParser object that has the config file read into it"""

    config = ConfigParser()
    config.read(CONFIG_FILE_NAME)

    return config


def setup_logging(logfile: str, log_format: str) -> None:
    """This function sets up the logging for both scripts, with the parameter deciding which file is to be used"""
    logging.basicConfig(filename=logfile, level=logging.DEBUG,
                        format=log_format)
    logging.captureWarnings(True)

    logging.info('Starting execution')


def ftp_connect(host: str, user: str, passwd: str, path: str) -> FTP:
    """Connect to the FTP server, change the working directory and return the connection"""

    logging.debug(f'Connecting to server {host}')
    # Login to the FTP server as the provided user
    ftp = FTP(host=host, user=user, passwd=passwd)

    # Change to the correct directory
    logging.debug(ftp.cwd(path))

    return ftp


def ftp_upload(path: str, filename: str, upload: FTP) -> None:
    with open(file=f'{path}{filename}', mode='rb') as file:
        logging.debug(upload.storbinary(f'STOR {filename}', file))
