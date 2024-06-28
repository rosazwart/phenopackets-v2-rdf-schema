import json
import os

def store_json_file(file_name: str, dict_values: dict):
    curr_wdir = os.getcwd()    
    file_path = os.path.join(curr_wdir, 'shacl2yarrrml', 'output', file_name)

    with open(file_path, 'w') as fp:
        json.dump(dict_values, fp, indent=4)
