import os
import sys
import pyshorteners


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
