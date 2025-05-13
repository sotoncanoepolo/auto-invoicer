#!/usr/bin/python

import sys
import os
from argparse import ArgumentParser

from dotenv import load_dotenv

# from lib.quickfile import find_client_id, create_invoice, get_invoice_info, get_client_balance, get_client_log_in
from lib.spreadsheet import Sheet
from lib.utils import ask_question, to_decimal_cost, shorten_link

import pandas as pd

# Load the CSV file
df1 = pd.read_csv('EmailDatabase.csv')

def search_person(query):
    # # Search for the query in the First Name, Last Name, and Username columns
    # results = df1[(df1['First Name'].str.contains(query, case=False, na=False)) |
    #              (df1['Last Name'].str.contains(query, case=False, na=False)) |
    #              (df1['Username'].str.contains(query, case=False, na=False))]

    # Split the query by spaces
    query_parts = query.split()
    if len(query_parts) == 1:
        # Search for the query in the First Name, Last Name, and Username columns
        results = df1[(df1['First Name'].str.contains(query_parts[0], case=False, na=False)) |
                     (df1['Last Name'].str.contains(query_parts[0], case=False, na=False)) |
                     (df1['Username'].str.contains(query_parts[0], case=False, na=False))]
    elif len(query_parts) == 2:
        # Search for the query parts in the First Name and Last Name columns
        results = df1[(df1['First Name'].str.contains(query_parts[0], case=False, na=False)) &
                     (df1['Last Name'].str.contains(query_parts[1], case=False, na=False))]
    elif len(query_parts) == 3:
        # Search for the query parts in the First Name, Middle Name, and Last Name columns
        results = df1[(df1['First Name'].str.contains(query_parts[0], case=False, na=False)) &
                     (df1['Last Name'].str.contains(query_parts[2], case=False, na=False))]
    else:
       results = df1[(df1['First Name'].str.contains(query_parts[0], case=False, na=False)) &
                    (df1['Last Name'].str.contains(query_parts[2], case=False, na=False))]


    if results.empty:
        return None
    
    if len(results) > 1:
        exact_match = results[results['Last Name'].str.lower() == query_parts[-1].lower()]
        if not exact_match.empty:
            email = exact_match.iloc[0]['Email']
            first_name = exact_match.iloc[0]['First Name']
            last_name = exact_match.iloc[0]['Last Name']
            username = exact_match.iloc[0]['Username']
            return (1,email, first_name, last_name, username)
        else:
            return (0, results[['First Name', 'Last Name', 'Username', 'Email']])

    email = results.iloc[0]['Email']
    first_name = results.iloc[0]['First Name']
    last_name = results.iloc[0]['Last Name']
    username = results.iloc[0]['Username']
    return (1,email, first_name, last_name, username)
    # return f"The email address for {query} is {email}."


# Load the spreadsheet
df2 = pd.read_excel('SUSU - Member Payments.xlsx', engine='openpyxl')

def search_person_link(first_name, last_name):
    # Search for the query in the First Name and Last Name columns
    results = df2[(df2['First Name'].str.contains(first_name, case=False, na=False)) &
                 (df2['Last Name'].str.contains(last_name, case=False, na=False))]

    if results.empty:
        return None
    
    if len(results) > 1:
        exact_match = results[results['Last Name'].str.lower() == last_name.lower()]
        if not exact_match.empty:
            return (exact_match.iloc[0]['Link'], exact_match.iloc[0]['Reference'])
        else:
            return None
    

    return (results.iloc[0]['Link'], results.iloc[0]['Reference'])

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

    PaymentDeadline = input("What is the payment deadline? ") # (DD/MM/YYYY) ")

    for person in people:
        person.paylink, person.payref = search_person_link(person.first_name, person.last_name)
        if person.paylink and isinstance(person.paylink, str):
            person.paylink = person.paylink.lstrip('\xa0')

    import requests

    # Power Automate webhook URL
    url = os.getenv("AUTOMAILER_API")

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
        print(payload)
        response = requests.post(url, json=payload)
        # Print the response
        print("Status Code:", response.status_code)
        print("Response:", response.text)

    
    

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
