import os
import sys
import pandas as pd
import json
from git import Repo

# path
#root_path = r'C:/Users/hitom/GitHubrepo/'
root_path = r'/Users/hashimoto/Githubrepo/'
folder_string = 'adjust_dataset'
dataset_string = 'Dataset_project'
result_string = 'Adjusted_Dataset'

sstubs_file = f'{root_path}{folder_string}/sstubs'
bugs_file = f'{root_path}{folder_string}/bugs.json'
dataset_project_path = f'{root_path}{dataset_string}/'

def read_json_file( filename ) :
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_file_content_at_commit(repo_path: str, commit_sha: str, file_path: str) -> str:
    """
    指定したコミット時点でのファイル内容（string）を取得する関数
    :param repo_path: ローカルにクローンした Git リポジトリのパス
    :param commit_sha: 親コミットなど、取得したいコミットのハッシュ
    :param file_path: リポジトリ内での相対パス（例: "src/main.py"）
    :return: str（ファイル内容）
    """
    repo = Repo(repo_path)
    commit = repo.commit(commit_sha)
    
    # ファイルの blob を取得する
    blob = commit.tree / file_path

    # blob.data_stream.read() は bytes なので decode する
    return blob.data_stream.read().decode("utf-8")

sstubs = read_json_file(sstubs_file)
df = pd.DataFrame(sstubs)
#print(df[df["projectName"] == "Activiti.Activiti"])

repo_name = "Activiti.Activiti"
project_name = "Activiti"
# project_nameに対応するデータを抽出
df_project = df[df["projectName"] == repo_name].copy()
# df_projectが空の場合はスキップ
if df_project.empty:
    print(f'Warning: No data for project {repo_name}. Skipping.')

# それぞれのファイルのSRCを取得
for row in df_project.iterrows():
    commit_sha = row["fixfixCommitParentSHA1"]
    file_path = row["bugFilePath"]
    try:
        src_content = get_file_content_at_commit(f'{dataset_project_path}{repo_name}', commit_sha, file_path)
        print(src_content)
    except Exception as e:
        print(f'Error retrieving file content for {file_path} at commit {commit_sha}: {e}')
        src_content = ""