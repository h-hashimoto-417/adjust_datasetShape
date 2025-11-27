import os
import sys
import pandas as pd
import json
import csv
from git import Repo
import difflib

# path
#root_path = r'C:/Users/hitom/GitHubrepo/'
root_path = r'/Users/hashimoto/Githubrepo/'
folder_string = 'adjust_dataset'
dataset_string = 'Dataset_project'
result_string = 'Dataset'


sstubs_file = f'{root_path}{folder_string}/sstubs'
bugs_file = f'{root_path}{folder_string}/bugs.json'
dataset_project_path = f'{root_path}{dataset_string}/'
dataset_csv_path = f'{root_path}{result_string}/File-level/'

def read_json_file( filename ) :
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def read_csv_file( filename ) :
    with open(filename, 'r', encoding='utf-8') as f:
        df = pd.read_csv(filename, index_col=False)
    return df


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

# sstubs = read_json_file(sstubs_file)
# df = pd.DataFrame(sstubs)
# #print(df[df["projectName"] == "Activiti.Activiti"])

# repo_name = "Activiti.Activiti"
# project_name = "Activiti"
# # project_nameに対応するデータを抽出
# df_project = df[df["projectName"] == repo_name].copy()
# # df_projectが空の場合はスキップ
# if df_project.empty:
#     print(f'Warning: No data for project {repo_name}. Skipping.')

# # それぞれのファイルのSRCを取得
# for index,row in df_project.iterrows():
#     commit_sha = row["fixCommitParentSHA1"]
#     file_path = row["bugFilePath"]
#     try:
#         src_content = get_file_content_at_commit(f'{dataset_project_path}{repo_name}', commit_sha, file_path)
#         print(src_content)
#     except Exception as e:
#         print(f'Error retrieving file content for {file_path} at commit {commit_sha}: {e}')
#         src_content = ""
        
 
def main():
    repo_name = "Activiti.Activiti"
    data = read_csv_file(f'{dataset_csv_path}{repo_name}-1.0.0_files_dataset.csv')
    df = pd.DataFrame(data)
    # 比較対象の文字列を取得
    text1 = df["SRC"].iloc[11] # .iloc[12] はインデックス番号12（13行目）を確実に取得
    text2 = df["SRC"].iloc[12] # .iloc[14] はインデックス番号14（15行目）を確実に取得

    if text1 == text2:
        print("same: 2つのSRCの内容は一言一句まで完全に一致しています。")
    else:
        print("different: 2つのSRCの内容は異なっています。")
        print("--- 差分の詳細 ---")
        
        # difflib.ndiff() を使用して差分を生成
        # 文字列を改行で区切ってリストに変換してから渡す（行単位の差分が分かりやすい）
        diff_generator = difflib.ndiff(text1.splitlines(), text2.splitlines())
        
        # 差分を表示
        for line in diff_generator:
            # '+ ' はtext2にのみ存在する行
            # '- ' はtext1にのみ存在する行
            # '? ' は変更があった行
            # '  ' は一致している行
            if line.startswith('+ ') or line.startswith('- ') or line.startswith('? '):
                print(line)
        print("----------------------")
if __name__ == "__main__":
    main()