import json

with open('mock_data/smog.json', 'r', encoding='utf-8') as json_data: 
    my_json = json.load(json_data)

print(my_json)