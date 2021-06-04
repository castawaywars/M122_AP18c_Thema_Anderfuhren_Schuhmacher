from ftplib import FTP
from datetime import datetime
import time

# The time to wait in seconds before executing the script.
WAIT_TIME = 5


def ftp_connect():
    print('Connecting to server...')
    ftp = FTP('localhost')  # TODO: Replace address with fixed remote host address
    # ftp.set_debuglevel(1)
    ftp.login()
    print(ftp.getwelcome())
    print(ftp.dir())
    return ftp


def ftp_download(ftp):
    print('Downloading...')
    filename = datetime.now().strftime("%d-%M-%Y_%H-%M-%S")
    print(filename)
    with open(f'{filename}.py', 'wb') as fp:
        print(ftp.retrbinary(f'RETR main.py', fp.write))
    return filename


def execute_file(filename):
    print('Opening and executing file')
    exec(open(f'{filename}.py').read())


if __name__ == '__main__':
    print(f'Entering wait duration of {WAIT_TIME} seconds...')
    time.sleep(WAIT_TIME)

    connection = ftp_connect()
    name = ftp_download(connection)
    connection.close()
    execute_file(name)
