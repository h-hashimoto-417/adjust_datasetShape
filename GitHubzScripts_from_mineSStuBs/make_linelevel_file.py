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
PROJECTS_NUM = 100
# global 変数
projects_yielded = 0

# 使用しないプロジェクト
skipped_projects = [
    'zxing.zxing', # no bugs
    'JakeWharton.ViewPagerIndicator', # no bugs
    'liaohuqiu.android-Ultra-Pull-To-Refresh', # no bugs
    'spring-projects.spring-mvc-showcase', # no bugs
    'spring-projects.spring-petclinic', # no bugs
    'jersey.jersey', # no commits
    'MyCATApache.Mycat-Server', # no bugs
    'dropwizard.metrics', # no commits
    'square.otto', # no bugs
    'b3log.solo', # no porject directory
    'JakeWharton.DiskLruCache', # no bugs
    'square.okio', # no bugs
    'checkstyle.checkstyle', # no commits
    'databricks.learning-spark', # no bugs
    'jfinal.jfinal', # no bugs
    'dangdangdotcom.elastic-job', # no bugs
    'alibaba.DataX', # no bugs
    'shuzheng.zheng', # no bugs
    'essentials.Essentials', # no bugs
    'kbastani.spring-cloud-microservice-example' # no bugs
]

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

def is_merge_commit(repo_path, commit_hash):
    cmd = [
        "git",
        "-C",
        repo_path,
        "rev-list",
        "--parents",
        "-n",
        "1",
        commit_hash,
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )

    parts = result.stdout.strip().split()
    # parts[0] が commit、自分以外が親
    return len(parts) > 2

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
        "-C",
        repo_path,
        "show",
        commit_hash,
        "-U0",
        "--",
        file_path,
    ]

    result = subprocess.run(
        cmd,
        
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


def get_modified_lines_from_merge_commit(repo_path, commit, parent_commit, file_path):
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
        "-C",
        repo_path,
        "diff",
        parent_commit,
        commit,
        "-U0",
        "--",
        file_path,
    ]

    result = subprocess.run(
        cmd,        
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



def read_diff_file(diff_text):
    """
    diffテキストを解析し、行ごとの情報を取得する関数
    :param diff_text: diffファイルの文字列
    :return: list of tuples (line_number,  length)
    """
    lines_info = []
    # @@ -a,b +c,d @@ を解析
    hunk_header = re.compile(r"@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@")

    for line in diff_text.splitlines():
        m = hunk_header.search(line)
        if not m:
            continue

        start = int(m.group(1))
        length = int(m.group(2) or 1)

        # 変更後に行が存在しない（削除のみ）の場合はスキップ
        if length == 0:
            continue
        lines_info.append((start, length))
    return lines_info

def check_bug_line_num(modified_lines, diff_file, bug_line_num):
    """
    diff_file内にmodified_linesが含まれているか確認する関数
    :param modified_lines: 修正行番号の list[int]
    :param diff_file: diffファイルの文字列
    :return: real_num: 実際にdiff内で修正されている行番号
    """
    
    for start, length in read_diff_file(diff_file):
        if bug_line_num >= start and bug_line_num < start + length:
            for modified_line in modified_lines:
                if modified_line >= start and modified_line < start + length:
                    return modified_line == bug_line_num, modified_line
    return False, -1
    
 
def is_duplicate_commit(df_project, repo_name, commit_sha, file_path, bug_line_num):
    # 同じファイル・行番号で、マージコミットでないバグ修正コミットが存在するか確認
    same_bugs = df_project[
        (df_project["bugFilePath"] == file_path) &
        (df_project["bugLineNum"] == bug_line_num) &
        (df_project["fixCommitSHA1"] != commit_sha)
    ]
    has_same_commit = False
    for _, sb_row in same_bugs.iterrows():
        sb_commit = sb_row["fixCommitSHA1"]
        if not is_merge_commit(f'{dataset_project_path}{repo_name}', sb_commit):
            has_same_commit = True
            break
    return has_same_commit


def make_dataset( data ):
    # projectごとにcsvファイルを生成
    # file_path, SRCをそれぞれ取得
    df = pd.DataFrame(data)
    for project_url in project_url_generator( projects_list_file, PROJECTS_NUM ):
         repo_name = get_project_repo_name( project_url )
         print (f'Processing project: {repo_name}')
         project_name = get_project_repo_name_hyphen( project_url )
         # repo_nameに対応するデータを抽出
         df_project = df[df["projectName"] == repo_name].copy()
         # df_projectが空の場合はスキップ
         if df_project.empty:
            print(f'Warning: No data for project {repo_name}. Skipping.')
            continue
         if os.path.isdir(f'{dataset_project_path}{repo_name}') is False:
            print(f'Warning: Project directory {dataset_project_path}{repo_name} does not exist. Skipping.')
            continue
         if repo_name in skipped_projects:
            print(f'Info: Project {repo_name} is in skipped projects list. Skipping.')
            continue

         ###### file-levelデータ作成 ######
         # 必要な列のみ抽出、列名変更
         df_filelevel = df_project[["bugFilePath"]].copy()
         df_filelevel = df_filelevel.rename(columns={"bugFilePath": "File"})
         # File列にproject_nameを追加
         #df_filelevel["File"] = project_name + "/" + df_filelevel["File"]
         # 今回はbugのあるファイルのみを扱う
         df_filelevel.insert(df_filelevel.columns.get_loc("File") + 1, "Bug", True)
         # それぞれのファイルのSRCを取得
         df_filelevel.insert(df_filelevel.columns.get_loc("Bug") + 1, "SRC", "")
         indexes_to_drop = []
         releases_indices = {1: []}
         release_on_file = {}
         df_filelevel_releases = {}
         for index,row in df_project.iterrows():
             commit_parent_sha = row["fixCommitParentSHA1"]
             commit_sha = row["fixCommitSHA1"]
             file_path = row["bugFilePath"]
             is_merge = is_merge_commit(f'{dataset_project_path}{repo_name}', commit_sha)
             if is_merge: 
                 # merge commitの場合はスキップ&削除
                 indexes_to_drop.append(index)
                 continue
             try:
                 src_content = get_file_content_at_commit(f'{dataset_project_path}{repo_name}', commit_parent_sha, file_path)
             except Exception as e:
                 print(f'Error retrieving file content for {file_path} at commit {commit_parent_sha}: {e}')
                 src_content = ""
             
             existing_file = df_filelevel[(df_filelevel["File"] == file_path) & (df_filelevel["SRC"] != "")]
             if existing_file.empty:
                 df_filelevel.loc[index, "SRC"] = src_content
                 releases_indices[1].append(index)
             elif (existing_file["SRC"] == src_content).any():
                samefile_index = existing_file[existing_file["SRC"] == src_content].index[0]
                key = next((k for k, v in releases_indices.items() if samefile_index in v), None)
                # 既に同じファイルパスで同じSRCが存在する場合、その行は削除対象とする
                indexes_to_drop.append(index)
                releases_indices[key].append(index) # 同じリリースに追加
             else:
                df_filelevel.loc[index, "SRC"] = src_content                   
                # リリースごとにインデックスを振り分けて管理
                if  file_path not in release_on_file.keys():
                    release_on_file[file_path] = 2
                else:
                    release_on_file[file_path] += 1
                if release_on_file[file_path] not in releases_indices.keys():
                    releases_indices[release_on_file[file_path]] = [index]
                else:
                    releases_indices[release_on_file[file_path]].append(index)
           
         for release_num, indices in releases_indices.items():
             df_filelevel_releases[release_num] = df_filelevel.loc[
                 (df_filelevel.index.isin(indices)) & (~df_filelevel.index.isin(indexes_to_drop))
             ]

         ###### line-levelデータ作成 ######
         # 必要な列のみ抽出、列名変更
         df_linelevel = df_project[["bugFilePath", "bugLineNum", "sourceBeforeFix", "bugType", "fixCommitSHA1"]].copy()
         df_linelevel = df_linelevel.rename(columns={"bugFilePath": "File", "bugLineNum": "Line_number", "sourceBeforeFix": "SRC"})    
         indexes_merge_commit = []
         indexes_notfound_linenum = []
         for index,row in df_project.iterrows():
             commit_sha = row["fixCommitSHA1"]
             file_path = row["bugFilePath"]
             diff_file = row["fixPatch"]
             bug_line_num = int(row["bugLineNum"])
             is_merge = is_merge_commit(f'{dataset_project_path}{repo_name}', commit_sha)
             if is_merge:
                 #print(f'Warning: Skipping merge commit {commit_sha} for project {repo_name}.')
                 # merge commitの場合はスキップ&削除
                 indexes_merge_commit.append(index)
                 continue
             try:
                 modified_lines = get_modified_lines_for_file(f'{dataset_project_path}{repo_name}', commit_sha, file_path)
             except Exception as e:
                 print(f'Error retrieving modified lines for {file_path} at commit {commit_sha}: {e}')
                 modified_lines = []
             
             is_correct_linenum, modified_line = check_bug_line_num(modified_lines, diff_file, bug_line_num)
             if not is_correct_linenum:
                 if modified_line == -1:
                     print(f'Warning: In project {repo_name}, for file {file_path} at commit {commit_sha}, bug line number {bug_line_num} not found in modified lines {modified_lines}.')
                     indexes_notfound_linenum.append(index)
                 else:
                     df_linelevel.loc[index, "Line_number"] = modified_line
              
         df_linelevel_releases = {}
         for release_num, indices in releases_indices.items():             
             df_linelevel_releases[release_num] = df_linelevel.loc[
                 df_linelevel.index.isin(indices) & (~df_linelevel.index.isin(indexes_merge_commit)) & (~df_linelevel.index.isin(indexes_notfound_linenum))
                 ]
         
         df_notfound = df_project.loc[indexes_notfound_linenum].copy()
         df_notfound = df_notfound[["projectName", "bugFilePath", "fixCommitSHA1", "bugLineNum", "bugType"]]
         if not df_notfound.empty:
             notfound_file = f'{repo_name}-notfound_linenum_bugs.csv'
             #save_csv(check_line_num_file_path, notfound_file, df_notfound)
         
         filelevel_csv_name = f'{repo_name}-1.0.0_files_dataset.csv'
         linelevel_csv_name = f'{repo_name}-1.0.0_defective_lines_dataset.csv'
        #  save_csv(file_level_path, filelevel_csv_name, df_filelevel)
        #  save_csv(line_level_path, linelevel_csv_name, df_linelevel)
         
         if df_filelevel_releases:
            for release_num, df_release in df_filelevel_releases.items():
                filelevel_csv_name_release = f'{repo_name}-{release_num}.0.0_files_dataset.csv'
                linelevel_csv_name_release = f'{repo_name}-{release_num}.0.0_defective_lines_dataset.csv'
                save_csv(file_level_path, filelevel_csv_name_release, df_release)
                save_csv(line_level_path, linelevel_csv_name_release, df_linelevel_releases[release_num])

         if os.path.isfile(f'{file_level_path}{filelevel_csv_name}') and os.path.isfile(f'{line_level_path}{linelevel_csv_name}'):
            global projects_yielded
            projects_yielded += 1
            print(f'Success: {project_name} file-level and line-level csv created.')
         else:
            print(f'Error: {project_name} csv not created.')
    


def main():    
    # jsonデータの読み込み
    jsondata = read_json_file(sstubs_file)

    make_dataset(jsondata)

if __name__ == "__main__":
    main()