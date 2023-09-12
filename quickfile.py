import os
import uuid
from datetime import datetime
from hashlib import md5
from typing import Final

import requests

from core import InvoiceItem
from utils import ask_question

base_api: Final[str] = "https://api.quickfile.co.uk/1_2"


def create_header() -> dict[str]:
    application_id = os.getenv("APPLICATION_ID")
    account_number = os.getenv("ACCOUNT_NUMBER")
    api_key = os.getenv("ACCOUNT_API_KEY")
    sub_number = str(uuid.uuid4())
    md5_hash = md5(bytes(account_number + api_key + sub_number, 'utf-8'))

    return {"MessageType": "Request", "SubmissionNumber": sub_number,
            "Authentication": {"AccNumber": account_number, "ApplicationID": application_id,
                               "MD5Value": md5_hash.hexdigest(), }}


def find_client_id(name: str) -> int:
    while True:
        payload = {"Header": create_header(), "Body": {
            "SearchParameters": {"ReturnCount": "1", "Offset": "0", "OrderResultsBy": "CompanyName",
                                 "OrderDirection": "ASC", "CompanyName": name}}}
        r = requests.post(base_api + "/Client/Search", json={"payload": payload})
        body = r.json()["Client_Search"]["Body"]
        record_set_count = body["RecordsetCount"]

        if record_set_count == 0:
            print(f'Could not find client with name: {name}, make sure to create a client on quickfile')
            ask_question("Should the search be retried with a different name?")
            name = input("Name: ")
        else:
            returned_client = body["Record"][0]
            returned_name = returned_client["CompanyName"]

            if record_set_count > 1:
                ask_question(f'Found {record_set_count} results for the following for client with name: {name}, '
                             f'should {returned_name} be used instead?')

            return returned_client["ClientID"]


def get_invoice_direct_url(invoice_id: int) -> str:
    payload = {
        "Header": create_header(),
        "Body": {
            "InvoiceID": str(invoice_id),
        }
    }
    r = requests.post(base_api + "/Invoice/Get", json={"payload": payload})
    body = r.json()["Invoice_Get"]["Body"]["InvoiceDetails"]

    return body["DirectPreviewUri"]


def create_invoice(client_id: int, invoice_name: str, items: list[InvoiceItem]) -> int:
    invoice_items = list(map(lambda item: item.to_invoice(), items))

    payload = {"Header": create_header(), "Body": {
        "InvoiceData": {"InvoiceType": "INVOICE", "ClientID": str(client_id), "Currency": "GBP", "TermDays": "14",
                        "Language": "en", "InvoiceDescription": invoice_name,
                        "InvoiceLines": {"ItemLines": {"ItemLine": invoice_items}},
                        "Scheduling": {"SingleInvoiceData": {"IssueDate": datetime.today().date().isoformat(), }}}}}
    r = requests.post(base_api + "/Invoice/Create", json={"payload": payload})
    body = r.json()["Invoice_Create"]["Body"]

    return body["InvoiceID"]
