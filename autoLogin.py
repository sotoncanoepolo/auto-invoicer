from argparse import ArgumentParser

from dotenv import load_dotenv

from lib.quickfile import get_client_log_in, find_client_id
from lib.utils import shorten_link


def main():
    load_dotenv()

    parser = ArgumentParser(prog='AutoLogin', description='Create a log in link for a specified person.')
    parser.add_argument('name', nargs='?')
    args = parser.parse_args()

    if args.name is None:
        args.name = input("Name: ")

    client_id = find_client_id(args.name)
    link = shorten_link(get_client_log_in(client_id))
    print(link)


if __name__ == '__main__':
    main()
