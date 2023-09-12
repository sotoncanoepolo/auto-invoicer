from argparse import ArgumentParser

from dotenv import load_dotenv

from quickfile import find_client_id, create_invoice, get_invoice_info
from spreadsheet import Sheet
from utils import ask_question, to_decimal_cost


def main():
    load_dotenv()

    parser = ArgumentParser(prog='AutoInvoicer', description='Generate invoices on quickfile from a spreadsheet')
    parser.add_argument('filename', help='the spreadsheet file')
    args = parser.parse_args()

    tournament_name = input("What is the tournament name? ")
    ask_question(f'Is {tournament_name} correct?')

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

        to_print += f'\n{person.name} - Owes £{total_cost} - Reference: {person.invoice_ref} - {person.direct_url}\n'

    print(to_print)


if __name__ == '__main__':
    main()
