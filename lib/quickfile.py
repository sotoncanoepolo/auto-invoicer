from dataclasses import dataclass
import os
import uuid
from datetime import datetime
from hashlib import md5
from typing import Final, List

import requests

from lib.core import InvoiceItem
from lib.utils import ask_question

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


@dataclass
class InvoiceInfo:
    invoice_ref: str
    direct_url: str


def get_invoice_info(invoice_id: int) -> InvoiceInfo:
    payload = {"Header": create_header(), "Body": {"InvoiceID": str(invoice_id)}}
    r = requests.post(base_api + "/Invoice/Get", json={"payload": payload})
    body = r.json()["Invoice_Get"]["Body"]["InvoiceDetails"]

    return InvoiceInfo(body["InvoiceNumber"], body["DirectPreviewUri"])


@dataclass
class InvoiceSearchInfo:
    invoice_ref: str
    invoice_id: int
    description: str
    client_id: int
    amount: int
    client_name: str


def get_aged_invoices() -> List[InvoiceSearchInfo]:
    payload = {"Header": create_header(), "Body": {"SearchParameters": {
        "ReturnCount": 200,
        "Offset": 0,
        "OrderResultsBy": "ClientName",
        "OrderDirection": "ASC",
        "InvoiceType": "INVOICE",
        "Status": "AGED",
    }}}
    invoices = list()
    while True:
        r = requests.post(base_api + "/Invoice/Search", json={"payload": payload})
        body = r.json()["Invoice_Search"]["Body"]

        for record in body["Record"]:
            amount = int(round(record["Amount"] * 100))
            invoices.append(InvoiceSearchInfo(record["InvoiceNumber"], record["InvoiceID"], record["Description"],
                                              record["ClientID"], amount, record["ClientCompanyName"]))

        if len(invoices) >= body["RecordsetCount"]:
            return invoices


def get_client_log_in(client_id: int, invoice_id: int = None) -> str:
    page = {}
    if invoice_id is not None:
        page["InvoiceView"] = {"InvoiceID": str(invoice_id)}
    else:
        page["Dashboard"] = "true"

    payload = {"Header": create_header(), "Body": {"ClientID": str(client_id), "LandingPage": page}}
    r = requests.post(base_api + "/Client/LogIn", json={"payload": payload})
    return r.json()["Client_LogIn"]["Body"]["RedirectUrl"]


def get_client_balance(client_id: int) -> int:
    payload = {"Header": create_header(), "Body": {"ClientID": str(client_id)}}
    r = requests.post(base_api + "/Client/Get", json={"payload": payload})
    body = r.json()["Client_Get"]["Body"]["BalanceTotals"]
    if body is None:
        return 0

    amount = body["Balance"][0]["Amount"]

    return int(round(amount * 100))


def create_invoice(client_id: int, invoice_name: str, items: list[InvoiceItem]) -> int:
    invoice_items = list(map(lambda item: item.to_invoice(), items))

    payload = {"Header": create_header(), "Body": {
        "InvoiceData": {"InvoiceType": "INVOICE", "ClientID": str(client_id), "Currency": "GBP", "TermDays": "7",
                        "Language": "en", "InvoiceDescription": invoice_name,
                        "InvoiceLines": {"ItemLines": {"ItemLine": invoice_items}},
                        "Scheduling": {"SingleInvoiceData": {"IssueDate": datetime.today().date().isoformat(), }}}}}
    r = requests.post(base_api + "/Invoice/Create", json={"payload": payload})
    body = r.json()["Invoice_Create"]["Body"]

    return body["InvoiceID"]
