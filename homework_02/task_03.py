import yaml


data_to_yaml = {
    "list": [3, 2, 1] ,
    "int": 555, 
    "dict": {
        "Dollar": "$", 
        "Euro": "€", 
        "Copyright": "©"
        }
    }

with open('data_write.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data_to_yaml, f, default_flow_style=False, allow_unicode=True)

with open('data_write.yaml', encoding='utf-8') as f_n:
    data_from_yaml = yaml.load(f_n, Loader=yaml.SafeLoader)


print(data_to_yaml == data_from_yaml)


