import random

# def get_proxy(id: int = None) -> str:
#     filename = 'proxy/iproyal-proxies.txt'
#     with open(filename, 'r') as file:
#         lines = [line.rstrip('\n') for line in file.readlines()]
#     if id:
#         proxy = lines[id]
#     else:
#         proxy = random.choice(lines)
#     return f'http://{proxy}'


def get_proxy(id: int = None) -> str:
    PROXY_USER = 'intexgroop'
    PROXY_PASS = '7529569_country-gb'
    PROXY_HOST = 'geo.iproyal.com'
    PROXY_PORT = 12321
    return f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'



