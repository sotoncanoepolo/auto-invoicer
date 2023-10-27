import sys
from argparse import ArgumentParser

from dotenv import load_dotenv

from lib.quickfile import find_client_id, create_invoice, get_invoice_info, get_client_balance
from lib.spreadsheet import Sheet
from lib.utils import ask_question, to_decimal_cost, shorten_link


def main():
    load_dotenv()

    parser = ArgumentParser(prog='AutoInvoicer', description='Generate invoices on quickfile from a spreadsheet')
    parser.add_argument('filename', help='the spreadsheet file')
    args = parser.parse_args()

    tournament_name = input("What is the tournament name? ")

    if len(tournament_name) > 35:
        print("Tournament name must be a maximum of 35 characters.")
        sys.exit(1)

    ask_question(f'Is {tournament_name} correct?')

    check_debt = ask_question(f'Should tournament debt be checked?', False)

    sheet = Sheet(args.filename)

    people = sheet.get_people()
    for person in people:
        sheet.add_costs(person)
    people_count = len(people)

    print(f'Found {people_count} people to invoice.')

    for person in people:
        person.client_id = find_client_id(person.name)

    print(f'Found the client IDs for all {people_count} people.')

    for person in people:
        person.invoice_id = create_invoice(person.client_id, tournament_name, person.costs)

    print(f'Created invoices for all {people_count} people.')
    ask_question("Please go to the quickfile interface, check all the created invoices and send them by email before "
                 "continuing. Continue?")

    to_print = (f'{tournament_name} Costs:\nYou can pay directly using the provided links, please make sure to include '
                f'the invoice reference if you are paying through other means.\n')
    for person in people:
        info = get_invoice_info(person.invoice_id)
        person.direct_url = info.direct_url
        person.invoice_ref = info.invoice_ref
        total_cost = to_decimal_cost(person.total_cost)
        link = shorten_link(person.direct_url)

        to_print += f'\n{person.name} - Owes £{total_cost} - Reference to use: {person.invoice_ref} - {link}\n'

        if check_debt and (balance := get_client_balance(person.client_id) is not None):
            person.outstanding_debts = balance
            to_print += f'Also Owes an extra £{to_decimal_cost(balance)}\n'

    if check_debt and any(map(lambda p: p.outstanding_debts is not None, people)):
        print(f'Some people also have club debts to settle. (Can be viewed by clicking accounts overview on '
              f'the invoice screen accessible using the link)\n')

    print(to_print)


if __name__ == '__main__':
    main()
