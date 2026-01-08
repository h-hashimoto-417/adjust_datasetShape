#!/usr/bin/python

import os
import sys
import pandas as pd
import json

# path
root_path = r'/Users/hashimoto/Githubrepo/'
folder_string = 'adjust_dataset'

tssb_dataset_folder = f'{root_path}{folder_string}/tssb_data_3M/'
projects_list_file = f'{root_path}{folder_string}/TSSBJavaProjects.csv'


dataset_json_file = [
    "file-0.jsonl",
    
]


def read_jsonl_file(filename):
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:  # 空行対策
                data.append(json.loads(line))
    return data

def save_csv(file_path, file_name, data):
    """
    Save result into f{file_path}{file_name}.
    :param file_path: The file location
    :param file_name: The file name
    :param data: The data
    :return:
    """
    make_path(file_path)
    # dataはpandasのDataFrame型を想定
    data.to_csv(f'{file_path}{file_name}', index=False, encoding="utf-8")
    #print(f'Result has been saved to {file_path}{file_name} successfully!')
    
def make_path(path):
    """
    Make path is it does not exists
    :param path:
    :return:
    """
    if not os.path.exists(path):
        os.makedirs(path)

def make_url_list( data ):
    url_list = set()
    for entry in data:
        repo_url = entry.get("project_url", "")
        if repo_url:
            url_list.add(repo_url)
    return url_list

def make_url_list_from_jsonfiles(  ):
    all_urls = set()
    for json_file in dataset_json_file:
        json_path = f'{tssb_dataset_folder}/{json_file}'
        data = read_jsonl_file( json_path )
        urls = make_url_list( data )
        all_urls.update( urls )
    
    save_csv( f'{root_path}{folder_string}/', "TSSBJavaProjects.csv", pd.DataFrame( list(all_urls), columns=['project_url'] ) )
    if os.path.isfile(f'{root_path}{folder_string}/TSSBJavaProjects.csv'):
        global projects_yielded
        projects_yielded += 1
        print(f'Success: TSSBJavaProjects.csv created.')
        print(f'  Total {len(all_urls)} project URLs saved.')
    else:
        print(f'Error: TSSBJavaProjects.csv not created.')

def main():
    if len(sys.argv) == 1:
        make_url_list_from_jsonfiles(  )

    elif sys.argv[1] == 'urls':
        make_url_list_from_jsonfiles(  )

if __name__ == '__main__':
    main(  )