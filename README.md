# Auto Invoicer

A bunch of useful scripts for interacting with quickfile and excel spreadsheets.

## Getting started

Clone the repository.

Auto Invoicer is tested to work on Python 3.11 and should be downloaded using your favourite package manager or using
the [python website](https://www.python.org/downloads/).

Create a `.env` file in the root directory and add the variables found in [`.env.example`](.env.example) modifying them
as required.

Download the python dependencies using the following command:

```bash
pip install -r requirements.txt
```

## autoInvoicer

This is the main script in this repository. It is used to generate quickfile invoices from an excel spreadsheet
following
a [template](https://sotonac.sharepoint.com/:x:/t/SUCP/EZ-8GlVY6cRNg1pZsiB3VooBjeUfU9S2Paw9yKQDDftDqA?e=3TcHhn).

The following headers are required to be in the excel spreadsheet: `Name`, `Refunds`, `Total Cost`, `Paid?`, `Notes`.

The following headers are optional but will be counted towards the total
invoiced: `Deposits`, `Entry`, `Camping`, `Food`, `Parking`, `Driver Debt`, `Cost towards travel`, `Travel Costs`, `Ferry Costs`.

Should you wish to add an extra cost not mentioned above the `normal_headers` variable can be updated
in [`lib/spreadsheet.py`](lib/spreadsheet.py)
on [this line](https://github.com/sotoncanoepolo/auto-invoicer/blob/a7c8f1cad3fd3a22a510b19a19ce8915a5aa30eb/lib/spreadsheet.py#L32).

```bash
python autoInvoicer.py [filepath to spreadsheet]
```

## Debts

Provides a list of users that have unpaid debts towards the club.

```bash
python debts.py
```

## autoLogin

Provides a passwordless link to a given customer's interface. 

```bash
python autoLogin.py [optional customer name to use]
```


