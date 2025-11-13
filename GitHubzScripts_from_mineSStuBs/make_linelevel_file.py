import os
import sys
import pandas as pd
import json
import csv


# path
root_path = r'C:/Users/hitom/GitHubrepo/'
folder_string = 'adjust_dataset'
dataset_string = 'Dataset_project'
result_string = 'Adjusted_Dataset'

sstubs_file = f'{root_path}{folder_string}/sstubs'
bugs_file = f'{root_path}{folder_string}/bugs'
projects_list_file = f'{root_path}{folder_string}/topJavaMavenProjects.csv'
file_level_path = f'{root_path}{folder_string}{result_string}/File-level/'
line_level_path = f'{root_path}{folder_string}{result_string}/Line-level/'
dataset_project_path = f'{root_path}{dataset_string}/'
# 定数
PROJECTS_NUM = 100
# global 変数
projects_yielded = 0

def read_json_file( filename ) :
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_project_repo_name( project_url ):
	user, project_name = project_url.split('/')[-2:]
	return '%s.%s' % (user, project_name)

def get_project_name( project_url ):
	project_name = project_url.split('/')[-1]
	return '%s' % (project_name)

def project_url_generator( projects_file, limit ):
	with open( projects_file, 'r' ) as projects:
		for line in projects:
			project_url = line.split(',')[0]
			if project_url == 'repository_url': continue
			yield project_url
			if projects_yielded >= limit: break

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
    for project_url in project_url_generator( projects_list_file, PROJECTS_NUM ):
         project_name = get_project_repo_name( project_url )
         print ('Processing project:'), project_name
         # project_nameに対応するデータを抽出
         df_project = df[df["projectName"] == project_name].copy()
         # 必要な列のみ抽出、列名変更
         df_dataset = df_project[["bugFilePath", "bugType"]].copy()
         df_dataset = df_dataset.rename(columns={"bugFilePath": "File"})
         # File列にproject_nameを追加
         df_dataset["File"] = project_name + "/" + df_dataset["File"]
         # 今回はbugのあるファイルのみを扱う
         df_dataset.insert(1, "Bug", True)

         save_csv(file_level_path, f'{get_project_name(project_url)}.csv', df_dataset)

         if os.path.isfile(f'{file_level_path}{get_project_name(project_url)}.csv'):
            global projects_yielded
            projects_yielded += 1
            print(f'Success: {project_name} file-level csv created.')
         else:
            print(f'Error: {project_name} file-level csv not created.')
    

def output_csv_linelevel( data ):
    # projectごとにcsvファイルを生成
    # file_path, Line_number, SRCをそれぞれ取得(bugtypeもあった方がいいかも)
    return

def main():    
    # jsonデータの読み込み
    jsondata = read_json_file(sstubs_file)

    output_csv_filelevel(jsondata)
    output_csv_linelevel(jsondata)

