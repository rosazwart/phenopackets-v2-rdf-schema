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
        self.matey_url = 'https://rml.io/yarrrml/matey/'
        self.driver = self.__setup_driver()

        self.get_rdf(rdf_instance_name, json_files, yarrrml_content, output_folder_levels)

    def __setup_driver(self):
        """  """ 
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(self.matey_url)

        print(f'Opened browser on {self.matey_url}')

        return driver
    
    def __add_input_file(self, json_filename: str):
        """  """
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
        """  """
        text_area_block = self.driver.find_element(By.CSS_SELECTOR, f'.ace-editor[data-matey-label="{json_filename}"]')

        text_area = text_area_block.find_element(By.CSS_SELECTOR, 'textarea')
        text_area.clear()
        print(f'Cleared textarea for {json_filename} as input file...')

        self.driver.execute_script("arguments[0].value = arguments[1];", text_area, json_data)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", text_area)
        print(f'Entered content of {json_filename} in textarea of input file...')

    def __fill_yarrrml_file(self, yarrrml_content: str):
        """  """
        text_area_block = self.driver.find_element(By.ID, 'editor-matey')

        text_area = text_area_block.find_element(By.CSS_SELECTOR, 'textarea')
        text_area.send_keys(Keys.CONTROL + 'a')
        text_area.send_keys(Keys.DELETE)
        print(f'Cleared textarea for YARRRML file...')

        self.driver.execute_script("arguments[0].value = arguments[1];", text_area, yarrrml_content)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", text_area)
        print(f'Entered YARRRML content in textarea of YARRRML file...')

    def __store_rdf(self, folder_levels: list, filename: str, rdf_text: str):
        """  """
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
        """  """
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
        """  """
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
        