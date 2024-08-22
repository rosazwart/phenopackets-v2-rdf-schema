import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

import jsonutil.loader as json_loader

class MateyScraper:
    def __init__(self, rdf_instance_name: str, json_files: list, yarrrml_content: str, output_folder_levels: list):
        """
            Automatically interacts with Matey. Adds input JSON files with the filenames corresponding to the names in YARRRML and the YARRRML file itself. The input is submitted and the output RDF is extracted and stored in a TTL file.

            :param rdf_instance_name: The name of the RDF dataset instance
            :datatype rdf_instance_name: str

            :param json_files: The list of JSON files represented by a dictionary holding all necessary information
            :datatype json_files: list

            :param yarrrml_content: The literal content of the YARRRML file
            :datatype yarrrml_content: str

            :param output_folder_levels: The path to the output folder represented in a list
            :datatype output_folder_levels: list
        """
        self.matey_url = 'https://rml.io/yarrrml/matey/'
        self.driver = self.__setup_driver()

        self.get_rdf(rdf_instance_name, json_files, yarrrml_content, output_folder_levels)

    def __setup_driver(self):
        """
            Set up the selenium driver for Chrome browsing the URL of Matey.

            :returns: The driver for interacting on a Chrome browser
            :rtype: webdriver.Chrome
        """ 
        chrome_options = Options()
        #chrome_options.add_argument('--headless')  # Add this option to hide the browser that is interacted with
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(self.matey_url)

        print(f'Opened browser on {self.matey_url}')

        return driver
    
    def __add_input_file(self, json_filename: str):
        """
            Add input file and submit the filename to Matey.

            :param json_filename: The name of the JSON file
            :datatype json_filename: str
        """
        input_btn = self.driver.find_element(By.ID, 'input-button-matey')
        input_btn.click()
        print('Clicked on button to show dropdown menu of input files...')

        create_btn = self.driver.find_element(By.ID, 'data-create-matey')
        create_btn.click()
        print('Clicked on button to add new input file...')

        input_alert = Alert(self.driver)
        input_alert.send_keys(json_filename)
        input_alert.accept()
        print(f'Entered {json_filename} as name of new input file...')

    def __fill_input_file(self, json_filename: str, json_data: str):
        """
            Fill the input file with the content of the corresponding JSON file.

            :param json_filename: The filename of the JSON file
            :datatype json_filename: str

            :param json_data: The literal content of the JSON file
            :datatype json_data: str
        """
        text_area_block = self.driver.find_element(By.CSS_SELECTOR, f'.ace-editor[data-matey-label="{json_filename}"]')

        text_area = text_area_block.find_element(By.CSS_SELECTOR, 'textarea')
        text_area.clear()
        print(f'Cleared textarea for {json_filename} as input file...')

        self.driver.execute_script("arguments[0].value = arguments[1];", text_area, json_data)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", text_area)
        print(f'Entered content of {json_filename} in textarea of input file...')

    def __fill_yarrrml_file(self, yarrrml_content: str):
        """
            Fill the input block for YARRRML with the literal content of the input YARRRML file.

            :param yarrrml_content: The literal content of the input YARRRML file
            :datatype yarrrml_content: str
        """
        text_area_block = self.driver.find_element(By.ID, 'editor-matey')

        text_area = text_area_block.find_element(By.CSS_SELECTOR, 'textarea')
        text_area.send_keys(Keys.CONTROL + 'a')
        text_area.send_keys(Keys.DELETE)
        print(f'Cleared textarea for YARRRML file...')

        self.driver.execute_script("arguments[0].value = arguments[1];", text_area, yarrrml_content)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", text_area)
        print(f'Entered YARRRML content in textarea of YARRRML file...')

    def __store_rdf(self, folder_levels: list, filename: str, rdf_text: str):
        """
            Extract the generated RDF content from the browser by accessing javascript variable value and store into a TTL file.

            :param folder_levels: The path to the folder in which the TTL file will be stored represented in a list
            :datatype folder_levels: list

            :param filename: The name of the TTL file
            :datatype filename: str

            :param rdf_text: The content of the generated RDF
            :datatype rdf_text: str
        """
        folder_path = os.getcwd()   
        for folder_level in folder_levels:
            folder_path = os.path.join(folder_path, folder_level)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path) 

        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(rdf_text)

        print(f'LD RDF lines have been written to {file_path}...')

    def __generate_ld_rdf(self):
        """ 
            Generate the RDF by clicking on the related submit button and retrieve the RDF data. The process is checked multiple times over a period of time to see whether the RDF is ready.

            :returns: Returns the generated RDF content or None if the RDF generation takes too long
            :rtype: None | str
        """
        generate_btn = self.driver.find_element(By.ID, 'ld-btn-matey')
        generate_btn.click()

        loop_limit = 15
        curr_loop_count = 0
        while True:
            print(f'Check whether LD RDF output is ready...')
            if curr_loop_count > loop_limit:
                break
            else:
                try:
                    _ = self.driver.find_element(By.CSS_SELECTOR, '.ace-editor[data-matey-label="output"]')
                except NoSuchElementException:
                    print(f'LD RDF output not ready yet, check again later...')
                else:
                    ld_result = self.driver.execute_script('return matey.editorManager.getLD();')
                    return ld_result[0]

                time.sleep(1)
                curr_loop_count += 1
        
        return None

    def get_rdf(self, rdf_instance_name: str, json_files: list, yarrrml_content: str, folder_levels: list):
        """
            Get the RDF file by interacting with Matey.

            :param rdf_instance_name: Name of the RDF dataset instance
            :datatype rdf_instance_name: str

            :param json_files: List of JSON files that are the input files
            :datatype json_files: list

            :param yarrrml_content: Content of YARRRML file that is used as input YARRRML
            :datatype yarrrml_content: str

            :param folder_levels: The path to the output folder represented in a list
            :datatype folder_levels: list
        """
        for json_file in json_files:
            json_filename, json_data = json_loader.extract_json_name_content(json_file)

            print(f'--- Add {json_filename} as input file ---')
            self.__add_input_file(json_filename)

            print(f'--- Fill content of {json_filename} in input file ---') 
            self.__fill_input_file(json_filename, json_data)

        print(f'--- Fill content of YARRRML file ---') 
        self.__fill_yarrrml_file(yarrrml_content)

        print(f'--- Generate Linked Data RDF ---') 
        rdf_data = self.__generate_ld_rdf()

        self.driver.quit()

        if rdf_data:
            self.__store_rdf(folder_levels=folder_levels, 
                             filename=f'{rdf_instance_name}.ttl', rdf_text=rdf_data)
        