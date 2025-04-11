import json
#
# with open('scripts/cardbase_crypt.json') as json_file:
# with open('scripts/cardbase_lib.json') as json_file:



with open('scripts/cardbase_crypt.json') as json_file:
    data = json.load(json_file)
    # print(len(data.keys()))
    print(data['200517'])
    print(data['201617'])
