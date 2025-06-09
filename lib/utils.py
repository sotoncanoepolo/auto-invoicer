import os
import sys
import pyshorteners
import msal
import requests
import pandas as pd


def ask_question(question: str, quit_program: bool = True) -> bool:
    while True:
        answer = input(question + " (Y/N): ").lower()
        match answer:
            case 'y' | 'yes':
                return True
            case 'n' | 'no':
                if quit_program:
                    sys.exit(1)
                else:
                    return False


def to_decimal_cost(cost: int) -> str:
    pounds = (abs(cost) // 100) * (1 if cost > 0 else -1)
    pence = abs(cost) % 100
    return f'{pounds}.{pence:02}'


def shorten_link(link: str) -> str:
    shortener = pyshorteners.Shortener(api_key=os.getenv("SHORT_API_KEY"), domain=os.getenv("SHORT_DOMAIN"))
    return shortener.shortcm.short(link)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# This script is used to search for people in a database to find their email and payment link.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


# Load the CSV file
df1 = pd.read_csv('EmailDatabase.csv')


def search_person(query):

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


def search_person_link(first_name, last_name, df2):
    # Search for the query in the First Name and Last Name columns
    results = df2[(df2['First Name'].str.contains(first_name, case=False, na=False)) &
                 (df2['Last Name'].str.contains(last_name, case=False, na=False))]
    # If no results are found, return None
    if results.empty:
        return None
    # If multiple results are found, check for an exact match on the last name
    if len(results) > 1:
        exact_match = results[results['Last Name'].str.lower() == last_name.lower()]
        if not exact_match.empty:
            return (exact_match.iloc[0]['Link'], exact_match.iloc[0]['Reference'])
        else:
            return None
    # If only one result is found, return the link and reference
    return (results.iloc[0]['Link'], results.iloc[0]['Reference'])


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# This script is used to send emails using Microsoft Graph API with device code flow authentication.
# It requires the Azure AD app credentials to be set in environment variables.
# The script allows sending emails with a custom body and invoice table.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# Azure AD app credentials
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPES = ['Mail.Send', 'Mail.Send.Shared', 'User.Read']


def get_access_token():
    """Authenticate using device code flow and return the access token."""
    app = msal.PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY)
    flow = app.initiate_device_flow(scopes=SCOPES)

    if 'user_code' not in flow:
        raise Exception("Failed to create device flow")

    print(f"Please go to {flow['verification_uri']} and enter the code: {flow['user_code']}")
    token_response = app.acquire_token_by_device_flow(flow)

    if 'access_token' in token_response:
        print("Authentication successful!")
        return token_response['access_token']
    else:
        print("Authentication failed:", token_response.get("error_description"))
        return None


def send_email(access_token, sender, recipient, subject, body):
    """Send an email using Microsoft Graph API."""
    url = f'https://graph.microsoft.com/v1.0/{sender}/sendMail'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    email_msg = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML", #"Text", # or "HTML" for HTML content
                "content": body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": recipient
                    }
                }
            ]
        },
        "saveToSentItems": "false"  # Set to "true" if you want to save the sent email in the Sent Items folder
    }

    response = requests.post(url, headers=headers, json=email_msg)
    print("Status:", response.status_code)
    print("Response:", response.text)


def make_invoice_table(invoice_lines):
    table = """
    <style>
      table {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
      }
      th, td {
        border: 1px solid #dddddd;
        text-align: left;
        padding: 8px;
      }
      th {
        background-color: #891b1b;
        color: white;
      }
      tr:nth-child(even) {
        background-color: #f2f2f2;
      }
    </style>
    <table>
      <tr>
        <th>Item</th>
        <th>Cost (£)</th>
      </tr>
    """
    for line in invoice_lines:
        table += f"<tr><td>{line['Item']}</td><td>{line['Cost']:.2f}</td></tr>"
    table += "</table>"
    return table


def create_email_body(name, preferred_name, email, tournament_name, total_cost, payment_link, invoice_lines, payment_deadline):
    body = f"""
    <p class="editor-paragraph">Hi {preferred_name},</p>

    <p class="editor-paragraph">
    Thank you for attending {tournament_name}.</p>

    <p class="editor-paragraph">
    The costs are as follows:</p>
    <p class="editor-paragraph"></p>
    <p class="editor-paragraph">Total Due: £{total_cost}</p>
    {make_invoice_table(invoice_lines)}
    <p class="editor-paragraph">Please pay the balance due as soon as possible, and no later than {payment_deadline}.</p>
    <p class="editor-paragraph">
    Payment Link: <a href="{payment_link}" class="editor-link">{payment_link}</a></p>
    <p class="editor-paragraph">Kind Regards,</p>
    <p class="editor-paragraph">SUCP Treasurer</p>
    <p class="editor-paragraph">
    ---</p>
    <p class="editor-paragraph">
    <i><em class="editor-text-italic">This is an automated email. The SUCP automailer system was created by Hari in 2025.</em></i>
    </p>
    """
    return body
