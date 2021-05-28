from ftplib import FTP
import time

WAIT_TIME = 5


def print_hi(name):
    print(f'Hi, {name}')


if __name__ == '__main__':
    print(f'Entering wait duration of {WAIT_TIME} seconds...')
    time.sleep(WAIT_TIME)
    print('Downloading new file...')
