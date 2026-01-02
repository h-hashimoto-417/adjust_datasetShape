import os
import sys
import pandas as pd
import json
import csv
from git import Repo
import subprocess
import re

# path
#root_path = r'C:/Users/hitom/GitHubrepo/'
root_path = r'/Users/hashimoto/Githubrepo/'
folder_string = 'adjust_dataset'
dataset_string = 'Dataset_project'
result_string = 'Adjusted_Dataset'

sstubs_file = f'{root_path}{folder_string}/sstubs'
bugs_file = f'{root_path}{folder_string}/bugs'
projects_list_file = f'{root_path}{folder_string}/topJavaMavenProjects.csv'
file_level_path = f'{root_path}{folder_string}/{result_string}/File-level/'
line_level_path = f'{root_path}{folder_string}/{result_string}/Line-level/'
dataset_project_path = f'{root_path}{dataset_string}/'

check_line_num_file_path = f'{root_path}{folder_string}/{result_string}/'

# 定数
PROJECTS_NUM = 3
# global 変数
projects_yielded = 0

def read_json_file( filename ) :
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_project_repo_name( project_url ):
	user, project_name = project_url.split('/')[-2:]
	return '%s.%s' % (user, project_name)

def get_project_repo_name_hyphen( project_url ):
	user, project_name = project_url.split('/')[-2:]
	return '%s-%s' % (user, project_name)

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


def get_modified_lines_for_file(repo_path, commit_hash, file_path):
    """
    指定コミット・指定ファイルで修正された
    「修正前ファイルの行番号」を返す

    :param repo_path: ローカルにクローンした Git リポジトリのパス
    :param commit_hash: コミットハッシュ
    :param file_path: リポジトリルートからの相対パス
    :return: 修正行番号の list[int]
    """
    cmd = [
        "git",
        "show",
        commit_hash,
        "-U0",
        "--",
        file_path,
    ]

    result = subprocess.run(
        cmd,
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )

    modified_lines = []

    # @@ -a,b +c,d @@ を解析
    hunk_header = re.compile(r"@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@")

    for line in result.stdout.splitlines():
        m = hunk_header.search(line)
        if not m:
            continue

        start = int(m.group(1))
        length = int(m.group(2) or 1)

        # 変更後に行が存在しない（削除のみ）の場合はスキップ
        if length == 0:
            continue

        modified_lines.extend(range(start, start + length))

    return modified_lines


def check_bug_line_num(data):
    df = pd.DataFrame(data)
    for project_url in project_url_generator( projects_list_file, PROJECTS_NUM ):
        repo_name = get_project_repo_name( project_url )
        print (f'Processing project: {repo_name}')
        df_project = df[df["projectName"] == repo_name].copy()
        if df_project.empty:
            print(f'Warning: No data for project {repo_name}. Skipping.')
            continue
        if os.path.isdir(f'{dataset_project_path}{repo_name}') is False:
            print(f'Warning: Project directory {dataset_project_path}{repo_name} does not exist. Skipping.')
            continue
        
        diff_linenum_bugs = []
        for index,row in df_project.iterrows():
            commit_sha = row["fixCommitSHA1"]
            file_path = row["bugFilePath"]            
            try:
                modified_lines = get_modified_lines_for_file(f'{dataset_project_path}{repo_name}', commit_sha, file_path)
            except Exception as e:
                print(f'Error retrieving modified lines for {file_path} at commit {commit_sha}: {e}')
                modified_lines = []
            bug_line_num = int(row["bugLineNum"])
            if bug_line_num not in modified_lines:
                print(f'Warning: In project {repo_name}, for file {file_path} at commit {commit_sha}, bug line number {bug_line_num} not found in modified lines {modified_lines}.')
                diff_linenum_bugs.append(index)
        
        df_diff = df_project.loc[diff_linenum_bugs].copy()
        df_diff = df_diff[["projectName", "bugFilePath", "fixCommitSHA1", "bugLineNum"]]
        if not df_diff.empty:
            check_line_num_file = f'{repo_name}-diff_bug_linenum.csv'
            save_csv(check_line_num_file_path, check_line_num_file, df_diff)
            print(f'{repo_name} line number were mismatched.')
        else:
            print(f'All bug line numbers matched for project {repo_name}.')
        
        global projects_yielded
        projects_yielded += 1
            

def main():    
    # jsonデータの読み込み
    jsondata = read_json_file(sstubs_file)

    check_bug_line_num(jsondata)

if __name__ == "__main__":
    main()    