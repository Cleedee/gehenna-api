import sys

from gehenna_api.utils.sources import select_search_strategy

if len(sys.argv) < 2:
    exit()

url = sys.argv[1]
slots = select_search_strategy(url)

