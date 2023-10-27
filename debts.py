from argparse import ArgumentParser
from typing import Dict, List

from dotenv import load_dotenv

from lib.quickfile import get_aged_invoices, InvoiceSearchInfo, get_client_log_in
from lib.utils import to_decimal_cost, shorten_link


def main():
    load_dotenv()

    parser = ArgumentParser(prog='Debts', description='Find any people with outstanding debts.')
    parser.parse_args()

    invoices = get_aged_invoices()
    clients: Dict[int, List[InvoiceSearchInfo]] = {}

    for invoice in invoices:
        clients.setdefault(invoice.client_id, []).append(invoice)

    print(f'Found {len(clients)} people with debts.')

    if len(clients) == 0:
        return

    to_print = (f'\nClub debts:\nYou can pay directly using the provided links, please make sure to include the invoice'
                f' reference if you are paying through other means.\nPlease contact me if you have any issues.\n')

    for client_id, invoices in clients.items():
        invoice_id = None
        total_debt = to_decimal_cost(sum(map(lambda i: i.amount, invoices)))
        if len(invoices) == 1:
            invoice_id = invoices[0].invoice_id

        name = invoices[0].client_name
        url = shorten_link(get_client_log_in(client_id, invoice_id))
        to_print += f'\n{name} - Owes £{total_debt} - {url}\n'

        for invoice in invoices:
            cost = to_decimal_cost(invoice.amount)
            to_print += f'      {invoice.description} - £{cost} - Reference to use: {invoice.invoice_ref}\n'

    print(to_print, end='')


if __name__ == '__main__':
    main()
