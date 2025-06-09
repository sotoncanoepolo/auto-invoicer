#!/usr/bin/python

import sys
import os
from argparse import ArgumentParser
from dotenv import load_dotenv
from lib.spreadsheet import Sheet
from lib.utils import ask_question, to_decimal_cost, shorten_link, get_access_token, send_email, create_email_body, search_person, search_person_link
import pandas as pd

# import requests # from old PowerAutomate based code

def main():
    load_dotenv()

    parser = ArgumentParser(prog='AutoMailer', description='Generate and sends cost breakdown emails from a spreadsheet')
    parser.add_argument('filename', help='the spreadsheet file')
    args = parser.parse_args()

    tournament_name = input("What is the tournament name? ")

    if len(tournament_name) > 35:
        print("Tournament name must be a maximum of 35 characters.")
        sys.exit(1)

    ask_question(f'Is {tournament_name} correct?')

    sheet = Sheet(args.filename)

    people = sheet.get_people()
    for person in people:
        sheet.add_costs(person)
    people_count = len(people)

    print(f'Found {people_count} people to invoice.')

    for person in people:
        foundemail = False
        query = person.name
        while foundemail is False:
            Response = search_person(query)
            if Response is not None:
                if Response[0] == 1:
                    person.email = Response[1]
                    person.first_name = Response[2]
                    person.last_name = Response[3]
                    person.username = Response[4]
                    print(f'Found email for {person.name}: {person.email}')
                    foundemail = True
                elif Response[0] == 0:
                    print(f'Multiple results found for {person.name}:')
                    print(Response[1])
                    print("Please refine your search.")
                    query = input("Enter the name or username to search: ")
            else:
                print(f'Could not find email for {person.name}.')
                answer = input("Should the search be retried with a different name? [Y/N]: ").lower()
                match answer:
                    case 'y' | 'yes':
                        query = input("Enter the name or username to search: ")
                    case 'n' | 'no':
                        ask_question("Do you want to enter the email/details manually?")
                        person.email = input("Email: ").lower()
                        person.firstname = input("SUSU Firstname: ")
                        person.surname = input("SUSU Surname: ")
                        person.username = "N/A"
                        print(f'Email for {person.name} set to {person.email}')
                        foundemail = True

    print(f'Found the emails for all {people_count} people.')
    
    FirstNames = []
    LastNames = []
    TotalCosts = []

    for person in people:
        # Create the CSV file for import to Money Hub
        FirstNames.append(person.first_name)
        LastNames.append(person.last_name)
        TotalCosts.append(to_decimal_cost(person.total_cost))

    # Sample data
    data = {
        'First Name': FirstNames,
        'Last Name': LastNames,
        'Cost': TotalCosts
    }
    print(TotalCosts)
    # Create DataFrame
    df3 = pd.DataFrame(data)

    # Save DataFrame to CSV
    df3.to_csv('CostDatabase.csv', index=False)

    print("CSV file 'CostDatabase.csv' has been created.")

    print(f'Created CostDatabase.csv for import to MH with costs for {people_count} people.')
    ask_question("Please upload the CSV file to Money Hub, check the costs and create payment requests before "
                 "continuing. Continue?")
    # Load the spreadsheet
    df2 = pd.read_excel('SUSU - Member Payments.xlsx', engine='openpyxl')

    PaymentDeadline = input("What is the payment deadline? ") # (DD/MM/YYYY) ")

    for person in people:
        person.paylink, person.payref = search_person_link(person.first_name, person.last_name, df2)
        if person.paylink and isinstance(person.paylink, str):
            person.paylink = person.paylink.lstrip('\xa0')


    # Power Automate webhook URL
    url = os.getenv("AUTOMAILER_API")

    access_token = get_access_token()
    if not access_token:
        print("Failed to get access token. Exiting.")
        sys.exit(1)

    sender = os.getenv("SENDER_EMAIL_ADDRESS") # format: 'users/<email_address>' for shared mailboxes, or 'me' for personal mailbox


    # Create the payload
    for person in people:
        
        payload = {
            "Name": person.name,
            "Preferred Name": person.first_name,
            "Email": person.email,
            "Tournament Name": tournament_name,
            "Total Cost": to_decimal_cost(person.total_cost),
            "Payment Link": person.paylink,
            "PaymentDeadline": PaymentDeadline,
            "Invoice Lines": [
                {
                    "Item": item_dict["ItemName"],
                    "Cost": float(item_dict["UnitCost"])
                }
                for item_dict in (invoice_item.to_invoice() for invoice_item in person.costs)
            ]
        }
        # print(payload)

        # # from old PowerAutomate based code:
        # response = requests.post(url, json=payload)
        # print("Status Code:", response.status_code)
        # print("Response:", response.text)

        recipient = person.email
        subject = f'{tournament_name} - Payment Request | SUCP'
        body = create_email_body(
            payload["Name"],
            payload["Preferred Name"],
            payload["Email"],
            payload["Tournament Name"],
            payload["Total Cost"],
            payload["Payment Link"],
            payload["Invoice Lines"],
            payload["PaymentDeadline"]
        )
        send_email(access_token, sender, recipient, subject, body)


    print(f'Created invoices for all {people_count} people.')
    ask_question("Please go to the club email account, and check all the emails have been sent correctly before "
                 "continuing. Continue?")

    to_print = (f'\n{tournament_name} Costs:\nPlease pay directly using the provided links, if you are having issues '
                f'please contact the Treasurer for assistance.\n')
    cost_table = ''

    for person in people:
        person.direct_url = person.paylink
        person.invoice_ref = person.payref
        total_cost = to_decimal_cost(person.total_cost)
       
        link = shorten_link(person.direct_url)
        cost_table += f'\n{person.name} - Owes £{total_cost} - Reference: {person.invoice_ref} - {link}\n'

    
    print(to_print)
    print(cost_table)


if __name__ == '__main__':
    main()
