import json
import os

RUN_DIR_NAME = 'example-phenopacket'

def get_all_json_filenames(dir_name: str = RUN_DIR_NAME):
    file_names = []

    curr_wdir = os.getcwd()
    for file_name in os.listdir(dir_name):
        file_path = os.path.join(curr_wdir, dir_name, file_name)
        if os.path.isfile(file_path) and '.json' in file_name:
            file_names.append(file_name)

    return file_names

def load_hamlet_json_file(filename: str):
    curr_wdir = os.getcwd()
    file_path = os.path.join(curr_wdir, RUN_DIR_NAME, filename)

    with open(file_path) as json_data:
        return json.load(json_data)
    
def store_json_file(foldername: str, filename: str, dict_values: dict):
    curr_wdir = os.getcwd()    

    folder_path = os.path.join(curr_wdir, 'jsonaligner', 'output', foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(curr_wdir, 'jsonaligner', 'output', folder_path, filename)

    with open(file_path, 'w') as fp:
        json.dump(dict_values, fp, indent=4)
