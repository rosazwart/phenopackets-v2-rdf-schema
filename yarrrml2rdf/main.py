import json
import os

import matey_scraper as matey_scraper

JSON_ALIGNER_FOLDERNAME = 'fdp_jsonaligner'
SHACL2YARRRML_FOLDERNAME = 'shacl2yarrrml'
RDF_OUTPUT_FOLDERNAME = 'example-fdp'

def load_json_files(folderpath: list):
    """  """
    path_to_json_folder = os.getcwd()
    
    for path_level in folderpath:
        path_to_json_folder = os.path.join(path_to_json_folder, path_level)
    
    json_files = []
    for filename in os.listdir(path_to_json_folder):
        file_path = os.path.join(path_to_json_folder, filename)
        if os.path.isfile(file_path) and '.json' in file_path:
            with open(file_path) as json_data:
                json_content = json.load(json_data)
                json_files.append({'filename': filename, 'content': json.dumps(json_content, indent=4)})
    
    return json_files

def load_yarrrml(folderpath: list):
    """  """
    path_to_yarrrml_folder = os.getcwd()
    
    for path_level in folderpath:
        path_to_yarrrml_folder = os.path.join(path_to_yarrrml_folder, path_level)
    
    for filename in os.listdir(path_to_yarrrml_folder):
        file_path = os.path.join(path_to_yarrrml_folder, filename)
        if os.path.isfile(file_path) and '.yaml' in file_path:
            with open(file_path, 'r') as file:
                return file.read()
            
def get_all_jsonaligner_output_names():
    instance_names = []

    curr_wdir = os.getcwd()
    output_folder_path = os.path.join(curr_wdir, JSON_ALIGNER_FOLDERNAME, 'output')

    for foldername in os.listdir(output_folder_path):
        folder_path = os.path.join(output_folder_path, foldername)
        if os.path.isdir(folder_path):
            instance_names.append(foldername)

    return instance_names

if __name__ == "__main__":
    jsonaligner_output_folder_levels = [JSON_ALIGNER_FOLDERNAME, 'output']
    shacl2yarrrml_output_folder_levels = [SHACL2YARRRML_FOLDERNAME, 'output']

    instance_names = get_all_jsonaligner_output_names()
    print(f'A total of {len(instance_names)} instances from the JSONAligner output ({"".join(jsonaligner_output_folder_levels)}) will be converted to RDF')
    for instance_name in instance_names:
        print(f'Convert JSON contents of instance {instance_name} to RDF using YARRRML from SHACL2YARRRML output ({"".join(shacl2yarrrml_output_folder_levels)})')
        yarrrml_content = load_yarrrml(folderpath=shacl2yarrrml_output_folder_levels)

        instance_folder_levels = jsonaligner_output_folder_levels + [instance_name]
        json_files = load_json_files(folderpath=instance_folder_levels)

        matey_scraper.MateyScraper(rdf_instance_name=instance_name,
                                   json_files=json_files, yarrrml_content=yarrrml_content,
                                   output_folder_levels=[RDF_OUTPUT_FOLDERNAME])
