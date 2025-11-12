import os
import sys
import pandas as pd
import json
import csv

from clone_top_maven_repos import project_url_generator

# path
root_path = r'C:/Users/hitom/GitHubrepo/'
folder_string = 'adjust_dataset'
dataset_string = 'Dataset_project'
result_string = 'Adjusted_Dataset'

sstubs_file = f'{root_path}{folder_string}/sstubs.json'
bugs_file = f'{root_path}{folder_string}/bugs.json'
projects_list_file = f'{root_path}{folder_string}/topJavaMavenProjects.csv'
file_level_path = f'{root_path}{folder_string}{result_string}/File-level/'
line_level_path = f'{root_path}{folder_string}{result_string}/Line-level/'
dataset_project_path = f'{root_path}{dataset_string}/'
# global 変数
projects_num = 100

def read_json_file( filename ) :
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_project_name( project_url ):
	project_name = project_url.split('/')[-1]
	return '%s' % (project_name)

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
    data.to_csv(f'{file_path}{file_name}', index=False, encoding="utf-8", newline="")
    #print(f'Result has been saved to {file_path}{file_name} successfully!')

def make_path(path):
    """
    Make path is it does not exists
    :param path:
    :return:
    """
    if not os.path.exists(path):
        os.makedirs(path)

def output_csv_filelevel( data ):
    # projectごとにcsvファイルを生成
    # file_path, SRCをそれぞれ取得
    df = pd.DataFrame(data)
    for project_url in project_url_generator( projects_list_file, projects_num ):
         project_name = get_project_name( project_url )
    

def output_csv_linelevel( data ):
    # projectごとにcsvファイルを生成
    # file_path, Line_number, SRCをそれぞれ取得(bugtypeもあった方がいいかも)
    return

def main():    
    # jsonデータの読み込み
    jsondata = read_json_file(sstubs_file)

    output_csv_filelevel(jsondata)
    output_csv_linelevel(jsondata)

