import sys


def ask_question(question: str):
    while True:
        answer = input(question + " (Y/N): ").lower()
        match answer:
            case 'y' | 'yes':
                return
            case 'n' | 'no':
                sys.exit(1)


def to_decimal_cost(cost: int) -> str:
    pounds = cost // 100
    pence = abs(cost) % 100
    return f'{pounds}.{pence:02}'
