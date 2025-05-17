import random

def get_proxy(id: int = None) -> str:
    filename = 'proxy/iproyal-proxies.txt'
    with open(filename, 'r') as file:
        lines = [line.rstrip('\n') for line in file.readlines()]
    if id:
        proxy = lines[id]
    else:
        proxy = random.choice(lines)
    return f'http://{proxy}'






