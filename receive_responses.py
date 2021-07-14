#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import os
import sys
import re
import smtplib
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.utils import make_msgid
from ftplib import FTP
from datetime import datetime
from zipfile import ZipFile, ZIP_LZMA, ZIP_STORED, ZIP_BZIP2, ZIP_DEFLATED

import shared


def get_receipts(download: FTP, upload: FTP):
    """Download all receipt files, extract their content and try to match every note file with the combined content
    in order to check if the invoice has already been processed"""

    # Get all receipt files and extract their content
    filenames = download.nlst()

    # This ensures that the combined content is correctly sorted
    filenames.sort()

    combined_content = ''

    for file in filenames:
        if file.startswith('quittungsfile') & file.endswith('.txt'):
            with open(file=f'{config["PATHS"]["pathtowait"]}{file}', mode='wb') as fp:
                logging.debug(download.retrbinary(f'RETR {file}', fp.write))

            with open(file=f'{config["PATHS"]["pathtowait"]}{file}', mode='r', errors='strict', encoding='UTF8') as f:
                receipt_file_content = f.read()
                combined_content += receipt_file_content

            # From here on, the receipt files are no longer needed on the server and get deleted to conserve performance
            logging.debug(download.delete(file))

    # Go through all note files and try to find their reference numbers in the combined content of the receipt files
    for file in os.listdir(config['PATHS']['pathtowait']):
        if file.endswith('_invoice.note'):
            logging.debug(f'Checking if the invoice belonging to {file} was already processed')
            with open(file=f'{config["PATHS"]["pathtowait"]}{file}', mode='r', errors='strict', encoding='UTF8') as f:
                note_file_content = f.read()

            split = note_file_content.split(';;')

            # Check if both output files have been processed
            match_txt = re.findall(pattern=rf'([0-9]+-[0-9]+)  {split[2]}_{split[0]}_invoice\.txt',
                                   string=combined_content, flags=re.IGNORECASE)
            match_xml = re.findall(pattern=rf'([0-9]+-[0-9]+)  {split[2]}_{split[0]}_invoice\.xml',
                                   string=combined_content, flags=re.IGNORECASE)

            if len(match_txt) == 0 & len(match_xml) == 0:
                logging.info(f'The invoice number {split[0]} has not yet been processed')
            else:
                message = f'The invoice number {split[0]} has been processed, sending confirmation'
                logging.info(message)
                print(message)

                # Generate and upload the ZIP file
                make_zip_file(split, upload)

                # Pass the email function the XML matches, because XML is usually processed after TXT
                send_email(split, match_xml)

                # Delete the note file to prevent it from being processed twice
                logging.debug(os.remove(f'{config["PATHS"]["pathtowait"]}{file}'))


def make_zip_file(note: list[str], upload: FTP) -> None:
    """Make a ZIP file with all relevant files, namely the TXT, the XML and the receipt, then upload it back to the
    customer server"""

    logging.debug('Creating ZIP file')

    pathconfig = config["PATHS"]
    filename = f'{note[2]}_{note[0]}_invoice'
    with ZipFile(f'{pathconfig["pathtoout"]}{filename}.zip', mode='w', compression=ZIP_DEFLATED) as z:
        # Put the files into the ZIP file and delete them afterwards
        logging.debug(z.write(f'{pathconfig["pathtoout"]}{filename}.txt'))
        logging.debug(os.remove(f'{pathconfig["pathtoout"]}{filename}.txt'))

        logging.debug(z.write(f'{pathconfig["pathtoout"]}{filename}.xml'))
        logging.debug(os.remove(f'{pathconfig["pathtoout"]}{filename}.xml'))

        # Get the receipt file
        for file in os.listdir(config['PATHS']['pathtowait']):
            if file.startswith('quittungsfile') & file.endswith('.txt'):
                logging.debug(z.write(f'{pathconfig["pathtowait"]}{file}'))
                # Since the receipt file is not needed anymore after this, delete it
                logging.debug(os.remove(f'{pathconfig["pathtowait"]}{file}'))

    shared.ftp_upload(config["PATHS"]["pathtoout"], f'{note[2]}_{note[0]}_invoice.zip', upload)


def send_email(note: list[str], match: list) -> None:
    """Extract the needed data from the note and the receipt, then send the confirmation email"""

    emailconfig = config['EMAIL']

    # Get the latest occurrence of this match and convert its date and time into a readable string
    date_time_split = str(match[len(match) - 1]).split('-')
    date = date_time_split[0]
    time = date_time_split[1]
    date_time = f'{date[6]}{date[7]}.{date[4]}{date[5]}.{date[0]}{date[1]}{date[2]}{date[3]} um ' \
                f'{time[0]}{time[1]}:{time[2]}{time[3]}:{time[4]}{time[5]}'

    # Define sender and recipient of the email
    sender = emailconfig['senderaddress']  # "Private Person <from@example.com>"
    receiver = note[3]  # "A Test User <to@example.com>"
    # Initialize the email and pass it all needed data
    message = EmailMessage()

    message['subject'] = f'Erfolgte Verarbeitung Rechnung {note[0]}'
    message['to'] = receiver
    message['from'] = sender
    message['date'] = datetime.now()
    message['message-id'] = make_msgid()

    # Prepare the email message content
    message.set_content(f'Sehr geehrte/r {note[4]}\n\nAm {date_time} wurde die erfolgreiche Bearbeitung der Rechnung '
                        f'{note[0]} vom Zahlungssystem "{config["FTP"]["paymenthost"]}" gemeldet.\n\n'
                        f'Mit freundlichen Grüssen\n\n{emailconfig["sendername"]}\n'
                        f'{emailconfig["companyname"]}')

    # Add the ZIP file with all its files to the email as attachment
    with open(file=f'{config["PATHS"]["pathtoout"]}{note[2]}_{note[0]}_invoice.zip', mode='rb') as fp:
        message.add_attachment(MIMEApplication(fp.read(), Name='archive.zip'))

    # Send the email
    with smtplib.SMTP(emailconfig['smtpaddress'], emailconfig.getint('smtpport')) as server:
        server.login(emailconfig['smtpuser'], emailconfig['smtppass'])
        server.sendmail(sender, receiver, message.as_bytes())


if __name__ == '__main__':
    def close_connections() -> None:
        """Close the connections if they are already established"""
        if 'connection_customer' in vars():
            connection_customer.quit()
        if 'connection_payment' in vars():
            connection_payment.quit()


    print('Running...')
    try:
        # Initialize the config
        config = shared.get_config()

        # Initialize logging
        shared.setup_logging(config['PATHS']['logfileout'], config['OTHER']['logformat'])

        # Establish the connections
        connection_customer = shared.ftp_connect(host=config['FTP']['customerhost'], user=config['FTP']['customeruser'],
                                                 passwd=config['FTP']['customerpass'],
                                                 path=f"in/{config['FTP']['customerpath']}")
        """The connection to the customer system"""

        connection_payment = shared.ftp_connect(host=config['FTP']['paymenthost'], user=config['FTP']['paymentuser'],
                                                passwd=config['FTP']['paymentpass'],
                                                path=f"out/{config['FTP']['paymentpath']}")
        """The connection to the payment system"""

        get_receipts(connection_payment, connection_customer)

        # Close the connections
        close_connections()

        print('Finished')
        logging.info('Finished')
    except Exception as e:
        print(f'Error: {str(e)}')
        logging.exception(e)
        # If the connections were already established, close them
        close_connections()
        sys.exit(1)
