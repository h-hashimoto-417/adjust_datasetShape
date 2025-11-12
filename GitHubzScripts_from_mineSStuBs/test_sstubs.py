import os
import sys
import pandas as pd
import json

# path
root_path = r'C:/Users/hitom/GitHubrepo/'
folder_string = 'adjust_dataset'
dataset_string = 'Dataset_project'
result_string = 'Adjusted_Dataset'

sstubs_file = f'{root_path}{folder_string}/sstubs.json'
bugs_file = f'{root_path}{folder_string}/bugs.json'

def read_json_file( filename ) :
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

sstubs = read_json_file(sstubs_file)
df = pd.DataFrame(sstubs)
print(df[df["projectName"] == "Activiti.Activiti"])