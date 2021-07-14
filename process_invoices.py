#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from decimal import Decimal
from ftplib import FTP

import shared

POSITION_SEPARATOR = '___'
"""This value separates individual invoice positions"""

VALUE_SEPARATOR = ';'
"""This symbol separates values of individual invoice positions"""


class ValueNotFoundError(Exception):
    """This error is to be raised when a value is required, but not found"""

    pass


def download_invoices(download: FTP, upload: FTP) -> None:
    """This function downloads all invoices from the server and then instantly analyses each one before continuing"""

    # Get all files in the directory
    filenames = download.nlst()

    # Download each file that ends with '.data' and then proceed to analyse it
    for file in filenames:
        try:
            if file.endswith('.data'):
                logging.info(f'Downloading {file}')
                with open(file=f'{config["PATHS"]["pathtoin"]}{file}', mode='wb') as fp:
                    logging.debug(download.retrbinary(f'RETR {file}', fp.write))
                output_files = analyse_file(file)

                # Upload the output files to the payment server
                shared.ftp_upload(config["PATHS"]["pathtoout"], f'{output_files}.txt', upload)
                shared.ftp_upload(config["PATHS"]["pathtoout"], f'{output_files}.xml', upload)

                print(f'Processed and uploaded {file}')

                # Delete the data file on the download server, to prevent it from being read again
                # TODO: Re-enable this when done developing
                # logging.debug(download.delete(file))

                # Delete the locally stored copy as well, as it is not needed anymore either
                logging.debug(os.remove(f'{config["PATHS"]["pathtoin"]}{file}'))
        except ValueNotFoundError as e:
            logging.error(e)
            print(str(e))


def analyse_file(filename: str) -> str:
    """Extract the data from the passed invoice file and generate the output files"""

    logging.info(f'Analyzing {filename}')
    try:
        file_content_text: str
        with open(file=f'{config["PATHS"]["pathtoin"]}{filename}', mode='r', errors='strict', encoding='UTF8') as f:
            file_content_text = f.read()
            extracted_content = extract_invoice_data(file_content_text)
            extracted_content['source_file_name'] = filename

            cost = generate_txt_file(extracted_content)
            generate_xml_file(extracted_content, cost)

            create_note_file(extracted_content)

            # Return the filename for the upload function
            return extracted_content['file_name']

    except ValueNotFoundError as value_error:
        raise type(value_error)(str(value_error) + f' in file "{filename}"').with_traceback(sys.exc_info()[2])


def extract_invoice_data(file: str) -> dict[str, str]:
    """Use regular expressions to extract all data from the invoice and store it in the dictionary"""

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
        file_values['payment_goal'] = regex_extractor(file, r';ZahlungszielInTagen_(\d\d)', 'Payment Date')

        # Second row
        file_values['sender_number'] = regex_extractor(file, r'Herkunft;([0-9]+);', 'Sender Number')
        file_values['sender_id'] = regex_extractor(file, r'Herkunft;[0-9]+;(K[0-9]+);', 'Sender ID')
        file_values['sender_name'] = regex_extractor(file, r'Herkunft;[0-9]+;[a-z0-9]+;([a-z &\u00F0-\u02AF]+);',
                                                     'Sender Name')
        file_values['sender_address'] = regex_extractor(file, r'Herkunft;[0-9]+;[a-z0-9]+;[a-z äöü]+;([a-z &\-'
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

        # Remove the last three characters to ensure that there is no empty position
        file_values['invoice_positions'] = combined_positions[:-3]

    except ValueNotFoundError as value_error:
        # When a ValueNotFoundError is raised, pass it further up to allow proper handling with all required information
        raise value_error
    except Exception as e:
        logging.exception('An error occurred while extracting data from a file')

    # Generate the name for the output files
    file_values['file_name'] = f'{file_values["sender_id"]}_{file_values["invoice_number"]}_invoice'

    return file_values


def regex_extractor(text: str, regex: str, required_name: str) -> str:
    """This function serves as a shortcut to use the pattern on the string and check for a missing result"""

    result = re.findall(pattern=regex, string=text, flags=re.IGNORECASE)

    if len(required_name) > 1 & len(result) < 1:
        raise ValueNotFoundError(f'Could not find required value "{required_name}"')
    else:
        return result[0]


def generate_txt_file(content: dict[str, str]) -> float:
    """Generate a TXT file from the provided content and save it"""

    # Prepare further content for the text file

    total_cost = 0.0

    invoice_positions = ''
    for raw_invoice_position in content['invoice_positions'].split(POSITION_SEPARATOR):
        split = raw_invoice_position.split(VALUE_SEPARATOR)

        # Check whether the total for a position equals the item cost multiplied by the count
        if int(split[2]) * float(split[3]) == float(split[4]):
            logging.info('Position total matches expected value')
        else:
            message = f'Discrepancy in {content["source_file_name"]} detected: Position {split[0]} total is {split[4]},' \
                      f' but should be {str(round(Decimal(int(split[2]) * float(split[3])), 2))}'
            logging.warning(message)
            print(message)

        invoice_position = f'  {split[0]}   {split[1]} {" " * (37 - len(split[1]))}{split[2]} ' \
                           f'{" " * (10 - len(split[3]))}{split[3]}  CHF {" " * (11 - len(split[4]))}{split[4]}  ' \
                           f'{split[5].split("_")[1]}'
        invoice_positions += invoice_position + '\n'
        total_cost += float(split[4])

    # Bring the total cost into a usable format
    string_total_cost = str(round(Decimal(total_cost), 2))

    # And format it again, this time with spaces
    string_total_cost_spaced = f'{string_total_cost.split(".")[0]} . {string_total_cost.split(".")[1]}'

    # Calculate the payment goal
    payment_goal = f'{content["payment_goal"]} Tage ' \
                   f'({(datetime.now() + timedelta(days=float(content["payment_goal"]))).strftime("%d.%m.%Y")})'

    # Generate the actual content of the text file
    text_file = f'\n\n\n\n{content["sender_name"]}\n{content["sender_address"]}\n{content["sender_place"]}\n\n' \
                f'{content["company_id"]}\n\n\n\n\nUster, den {datetime.now().strftime("%d.%m.%Y")}' \
                f'                            {content["recipient_name"]}\n' \
                f'                                                 {content["recipient_address"]}\n' \
                f'                                                 {content["recipient_place"]}\n\nKundennummer:' \
                f'      {content["sender_id"]}\nAuftragsnummer:    {content["order_number"]}\n\nRechnung Nr' \
                f'       {content["invoice_number"]}\n-----------------------\n{invoice_positions}' \
                f'                                                              -----------\n' \
                f'                                                Total CHF         {string_total_cost}\n\n' \
                f'                                                MWST  CHF            0.00\n' \
                f'{chr(10) * (18 - len(content["invoice_positions"].split("___")))}' \
                f'Zahlungsziel ohne Abzug {payment_goal}\n\nEinzahlungsschein\n\n\n\n\n\n\n\n\n\n\n\n' \
                f'    {string_total_cost_spaced}                    {string_total_cost_spaced}     ' \
                f'{content["recipient_name"]}\n' \
                f'                                               {content["recipient_address"]}\n' \
                f'0 00000 00000 00000                            {content["recipient_place"]}\n\n' \
                f'{content["recipient_name"]}\n{content["recipient_address"]}\n{content["recipient_place"]}'

    with open(file=f'{config["PATHS"]["pathtoout"]}{content["file_name"]}.txt', mode='w') as fp:
        logging.debug(fp.write(text_file))

    # Return the calculated total cost, so the XML function can use it
    return total_cost


def generate_xml_file(content: dict[str, str], total_cost: float) -> None:
    """Generate a TXT file by filling the template with the provided content and save it"""

    # Get the template
    tree = ET.parse('xml_invoice_template.xml')
    root = tree.getroot()

    date = datetime.now().strftime('%Y%m%d')

    # Fill in the data
    root[0][0][0].text = content['sender_number']
    root[0][1][0].text = content['customer_id']
    root[1][0][1][0][0].text = datetime.now().strftime('%Y%m%d%H%M%S')
    root[1][0][1][0][1].text = date
    root[1][0][2][0].text = date
    root[1][0][3][0][0][0].text = content['invoice_number']
    root[1][0][3][0][0][1].text = date
    root[1][0][3][1][0][0].text = content['order_number']
    root[1][0][3][1][0][1].text = date
    root[1][0][3][3][0][1].text = date
    root[1][0][4][0].text = content['company_id']
    root[1][0][4][2][0].text = content['sender_number']
    root[1][0][4][3][0][0].text = content['sender_name']
    root[1][0][4][3][0][1].text = content['sender_address']
    root[1][0][4][3][0][2].text = content['sender_place']
    root[1][0][5][0][0].text = content['customer_id']
    root[1][0][5][1][0][0].text = content['sender_name']
    root[1][0][5][1][0][1].text = content['sender_address']
    root[1][0][5][1][0][2].text = content['sender_place']
    root[1][2][0][0].text = str(int((total_cost * 100))).zfill(10)
    root[1][2][5][0][0][0].text = content['payment_goal']
    root[1][2][5][0][0][1].text = (datetime.now() + timedelta(days=float(content["payment_goal"]))).strftime("%d.%m.%Y")

    # Save the new file
    logging.debug(tree.write(f'{config["PATHS"]["pathtoout"]}{content["file_name"]}.xml'))


def create_note_file(content: dict[str, str]) -> None:
    """Create a note file that reminds the system to fetch the confirmation for successful processing"""

    note_file = f'{content["invoice_number"]};;{content["order_number"]};;{content["sender_id"]};;' \
                f'{content["email"]};;{content["sender_name"]}'

    with open(file=f'{config["PATHS"]["pathtowait"]}{content["file_name"]}.note', mode='w') as fp:
        logging.debug(fp.write(note_file))


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
        shared.setup_logging(config['PATHS']['logfilein'], config['OTHER']['logformat'])

        # Establish the connections
        connection_customer = shared.ftp_connect(host=config['FTP']['customerhost'], user=config['FTP']['customeruser'],
                                                 passwd=config['FTP']['customerpass'],
                                                 path=f"/out/{config['FTP']['customerpath']}")
        """The connection to the customer system"""

        connection_payment = shared.ftp_connect(host=config['FTP']['paymenthost'], user=config['FTP']['paymentuser'],
                                                passwd=config['FTP']['paymentpass'],
                                                path=f"/in/{config['FTP']['paymentpath']}")
        """The connection to the payment system"""

        download_invoices(connection_customer, connection_payment)

        # Close the connections
        close_connections()

        print('Finished')
        logging.info('Finished')
    except KeyError as e:
        logging.exception(e)
        print(f'Could not find config value with name {str(e)}')
    except Exception as e:
        print(f'Error: {str(e)}')
        logging.exception(e)
        # If the connections were already established, close them
        close_connections()
        sys.exit(1)
