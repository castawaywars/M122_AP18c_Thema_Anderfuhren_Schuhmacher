#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import re
import sys
from datetime import datetime, timedelta
from ftplib import FTP

PATH_TO_FILES = '.\\files\\'


class ValueNotFoundError(Exception):
    """This error is to be raised when a value is required, but not found"""

    pass


def ftp_connect():
    """Connect to the FTP server and return the connection"""

    logging.debug('Connecting to server...')
    # Login to the FTP server as the provided user
    ftp = FTP(host='ftp.haraldmueller.ch', user='schoolerinvoices', passwd='Berufsschule8005!')

    # Change to the correct directory
    ftp.cwd('/out/AP18cSchuhmacher')

    return ftp


def ftp_download(ftp: FTP):
    """Download all available files from the FTP server and then delete them to prevent multiple reads"""

    # Get all files in the directory
    filenames = ftp.nlst()

    # Download each file that ends with '.data' and then proceed to analyse it
    for file in filenames:
        try:
            if file.endswith('.data'):
                logging.info(f'Downloading {file}')
                with open(file=f'{PATH_TO_FILES}{file}', mode='wb') as fp:
                    logging.debug(ftp.retrbinary(f'RETR {file}', fp.write))
                analyse_file(file)
        except ValueNotFoundError as e:
            logging.exception(e)
            print(str(e))


def analyse_file(filename: str):
    """Extract the data of all invoice files currently stored in the files directory"""

    try:
        file_content_text: str
        with open(file=f'{PATH_TO_FILES}{filename}', mode='r', errors='strict', encoding='UTF8') as f:
            file_content_text = f.read()
            print(file_content_text)
            extracted_content = extract_invoice_data(file_content_text)
            generate_txt_file(extracted_content)

    except ValueNotFoundError as value_error:
        raise type(value_error)(str(value_error) + f' in file "{filename}"').with_traceback(sys.exc_info()[2])


def extract_invoice_data(file: str) -> dict[str, str]:
    """Extract the data from a single invoice data file"""

    file_values: dict[str, str] = dict[str, str]()

    try:
        # First row
        file_values['invoice_number'] = regex_extractor(file, r'Rechnung_([0-9]+);', 'Invoice Number')
        file_values['order_number'] = regex_extractor(file, r'Auftrag_(A[0-9]+);', 'Order Number')
        file_values['generation_place'] = regex_extractor(file, r'[a-z_0-9]+;[a-z_0-9]+;([a-z\u00F0-\u02AF]+);',
                                                          'Generation Place')
        file_values['generation_date'] = regex_extractor(file, r'[a-z_0-9]+;[a-z_0-9]+;[[a-z\u00F0-\u02AF]+;('
                                                               r'\d\d\.\d\d\.\d\d\d\d);', 'Generation Date')
        file_values['generation_time'] = regex_extractor(file, r'[a-z_0-9]+;[a-z_0-9]+;[['
                                                               r'a-z\u00F0-\u02AF]+;\d\d\.\d\d\.\d\d\d\d;('
                                                               r'\d\d:\d\d:\d\d);', 'Generation Time')
        file_values['payment_date'] = regex_extractor(file, r';ZahlungszielInTagen_(\d\d)', 'Payment Date')

        # Second row
        file_values['sender_number'] = regex_extractor(file, r'Herkunft;([0-9]+);', 'Sender Number')
        file_values['sender_id'] = regex_extractor(file, r'Herkunft;[0-9]+;(K[0-9]+);', 'Sender ID')
        file_values['sender_name'] = regex_extractor(file, r'Herkunft;[0-9]+;[a-z0-9]+;([a-z &\u00F0-\u02AF]+);',
                                                     'Sender Name')
        file_values['sender_address'] = regex_extractor(file, r'uHerkunft;[0-9]+;[a-z0-9]+;[a-z äöü]+;([a-z &\-'
                                                              r'\u00F0-\u02AF0-9]+);', 'Sender Address')
        file_values['sender_place'] = regex_extractor(file, r'Herkunft;[0-9]+;[a-z0-9]+;[a-z äöü]+;[a-z &\-'
                                                            r'\u00F0-\u02AF0-9]+;([a-z \u00F0-\u02AF0-9]+);',
                                                      'Sender Place')
        file_values['company_id'] = regex_extractor(file, r'Herkunft;[0-9]+;[a-z0-9]+;[a-z äöü]+;[a-z &\-'
                                                          r'\u00F0-\u02AF0-9]+;[a-z \u00F0-\u02AF0-9]+;([a-z\-0-9\.'
                                                          r' ]+);', 'Company ID')
        file_values['email'] = regex_extractor(file, r';([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', 'Email')

        # Third row
        file_values['customer_id'] = regex_extractor(file, r'Endkunde;([0-9]+);', 'Customer ID')
        file_values['recipient_name'] = regex_extractor(file, r'Endkunde;[0-9]+;([a-z0-9 \u00F0-\u02AF]+);',
                                                        'Recepient Name')
        file_values['recipient_address'] = regex_extractor(file, r'Endkunde;[0-9]+;[a-z0-9 \u00F0-\u02AF]+;([a-z0-9 '
                                                                 r'\u00F0-\u02AF]+);', 'Recepient Address')
        file_values['recipient_place'] = regex_extractor(file, r'Endkunde;[0-9]+;[a-z0-9 \u00F0-\u02AF]+;[a-z0-9 '
                                                               r'\u00F0-\u02AF]+;([a-z0-9 \u00F0-\u02AF]+)',
                                                         'Recepient Place')

        # Get the invoice positions
        positions: list[str] = re.findall(r'RechnPos;([1-9][0-9]?;[a-z0-9\- &\u00F0-\u02AF]+;[1-9][0-9]?;[1-9]['
                                          r'0-9]*\.[0-9]{2};[1-9][0-9]*\.[0-9]{2};[a-z0-9\-._% &\u00F0-\u02AF]+)',
                                          file, flags=re.IGNORECASE)
        if len(positions) < 1:
            raise ValueNotFoundError('Could not find invoice positions')

        combined_positions = ''
        for position in positions:
            combined_positions += position + '___'

        file_values['invoice_positions'] = combined_positions

    except ValueNotFoundError as value_error:
        # When a ValueNotFoundError is raised, pass it further up to allow proper handling with all required information
        raise value_error
    except Exception as e:
        logging.exception('An error occurred while extracting data from a file')

    print(file_values)
    return file_values


def regex_extractor(text: str, regex: str, required_name: str) -> str:
    result = re.findall(regex, text, flags=re.IGNORECASE)

    if len(required_name) > 1 & len(result) < 1:
        raise ValueNotFoundError(f'Could not find required value "{required_name}"')
    else:
        return result[0]


def generate_txt_file(content: dict[str, str]):
    """Generate a TXT file from the provided content and save it"""

    # Prepare further content for the text file

    total_cost = 0

    invoice_positions = ''
    for raw_invoice_position in content['invoice_positions'].split('___'):
        split = raw_invoice_position.split(';')
        invoice_position = f'  {split[0]}   {split[1]} {" " * (37 - len(split[1]))}{split[2]} ' \
                           f'{" " * (10 - len(split[3]))}{split[3]} {" " * (16 - len(split[4]))}  0.00%'
        invoice_positions += invoice_position + '\n'
        total_cost += float(split[4])

    # Fill the space between the parts of the invoice up with empty lines to ensure proper spacing
    spacer = ''
    i = 0
    while i < (16 - len(invoice_positions)):
        spacer += '\n'

    payment_goal = f'{content["payment_goal"]} Tage ' \
                   f'({(datetime.now() + timedelta(days=float(content["payment_goal"]))).strftime("%d.%M.%Y")})'

    # Generate the actual content of the text file
    text_file = f'\n\n\n\n{content["sender_name"]}\n{content["sender_address"]}\n{content["sender_place"]}\n\n' \
                f'content["company_id"]\n\n\n\n\nUster, den {datetime.now().strftime("%d.%M.%Y")}' \
                f'                            {content["recipient_name"]}\n' \
                f'                                                 {content["recipient_address"]}\n' \
                f'                                                 {content["recipient_place"]}\nKundennummer:' \
                f'      {content["sender_id"]}\nAuftragsnummer:    {content["order_number"]}\n\nRechnung Nr' \
                f'       {content["invoice_number"]}\n-----------------------\n{invoice_positions}' \
                f'                                                              -----------\n' \
                f'                                                Total CHF         {total_cost}\n\n' \
                f'                                                MWST  CHF            0.00\n\n\n\n\n\n\n\n\n\n\n\n\n' \
                f'Zahlungsziel ohne Abzug {payment_goal}\nEinzahlungsschein\n\n\n\n\n\n\n\n\n\n\n\n' \
                f'    {total_cost}                    {total_cost}     {content["recipient_name"]}\n' \
                f'                                               {content["recipient_address"]}\n' \
                f'0 00000 00000 00000                            {content["recipient_place"]}\n\n' \
                f'{content["recipient_name"]}\n{content["recipient_address"]}\n{content["recipient_place"]}'

    print(text_file)
    with open(file=f'{PATH_TO_FILES}{content["sender_id"]}_{content["invoice_number"]}_invoice.txt', mode='wb') as fp:
        logging.debug(fp.writelines(text_file))


def generate_xml_file(content: dict[str, str]):
    """Generate a TXT file by filling the template with the provided content and save it"""

    xml_file = f''


if __name__ == '__main__':
    print('Running...')
    try:
        # Initialize logging
        logging.basicConfig(filename='process_invoices_logs.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
        logging.captureWarnings(True)

        # Start the execution
        connection_customer = ftp_connect()
        ftp_download(connection_customer)
        """The connection to the customer system"""

    except Exception as e:
        print(f'Error: {e}')
        logging.exception('An error occurred')
        sys.exit(1)
