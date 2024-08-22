import os
import json

def extract_json_name_content(json_file: dict):
    """
        Extract the information from a dictionary holding information about a JSON file.

        :param json_file: Dictionary holding information about JSON file
        :datatype json_file: dict

        :returns: The name of the JSON file and the content 
        :rtype: str, dict
    """
    return json_file['filename'], json_file['content']
        
def load_json_files(folderpath: list):
    """
        Load all aligned JSON files found in given folder.

        :param folderpath: Path to folder containing the needed JSON files that are correctly aligned in order to work with the YARRRML file
        :datatype folderpath: list

        :returns: List of all JSON files represented as a dictionary
        :rtype: List[dict]
    """
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