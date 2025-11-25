import os
import base64
import json
import requests
from target_packages import TARGET_PACKAGES

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG = os.getenv("ORG")
TEAM_SLUG = os.getenv("TEAM_SLUG")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def get_team_repos():
    """Team 配下のすべてのリポジトリを取得"""
    url = f"https://api.github.com/orgs/{ORG}/teams/{TEAM_SLUG}/repos"
    repos = []
    page = 1

    while True:
        r = requests.get(url, headers=HEADERS, params={"page": page, "per_page": 100})
        if r.status_code != 200:
            raise Exception(f"Error fetching repos: {r.text}")
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1

    return repos


def get_all_package_lock_paths(repo_full_name):
    """リポジトリ内のすべての package-lock.json のパスを再帰的に取得"""
    url = f"https://api.github.com/repos/{repo_full_name}/git/trees/HEAD?recursive=1"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"Error fetching tree for {repo_full_name}: {r.text}")
        return []
    tree = r.json().get("tree", [])
    return [item["path"] for item in tree if item["path"].endswith("package-lock.json")]


def get_package_lock_json(repo_full_name, path):
    """指定リポジトリ・パスの package-lock.json を取得"""
    url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        print(f"Error fetching {repo_full_name}:{path}: {r.text}")
        return None
    content = r.json().get("content")
    return json.loads(base64.b64decode(content).decode("utf-8"))


def scan_repo(repo):
    """リポジトリ内のすべての package-lock.json を走査し、該当パッケージを返す"""
    repo_full_name = repo["full_name"]
    lock_paths = get_all_package_lock_paths(repo_full_name)
    found = []

    for path in lock_paths:
        lock_json = get_package_lock_json(repo_full_name, path)
        if lock_json is None:
            continue
        packages = lock_json.get("packages", {})
        matched_pkgs = []
        for target in TARGET_PACKAGES:
            pkg_name = target["name"]
            target_version = target["version"]
            pkg_lock_entry = packages.get(f"node_modules/{pkg_name}")
            if pkg_lock_entry:
                version = pkg_lock_entry.get("version")
                if version == target_version:
                    matched_pkgs.append((pkg_name, version))
        if matched_pkgs:
            found.append((path, matched_pkgs))
    return found


def main():
    print("Fetching team repositories...\n")
    repos = get_team_repos()

    result = {}

    for repo in repos:
        full_name = repo["full_name"]
        print(f"Scanning {full_name}...")

        matches = scan_repo(repo)
        if matches:
            result[full_name] = matches

    print("\n=== Scan Result ===")
    if not result:
        print("No repositories found using the target packages.")
    else:
        for repo, files in result.items():
            print(f"\n📌 {repo}")
            for path, pkgs in files:
                print(f"  - Found in: {path}")
                for pkg, ver in pkgs:
                    print(f"    - {pkg}@{ver}")


if __name__ == "__main__":
    main()
