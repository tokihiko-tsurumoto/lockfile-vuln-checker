import os
import base64
import json
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG = os.getenv("ORG")
TEAM_SLUG = os.getenv("TEAM_SLUG")

TARGET_PACKAGES = {
    "@accordproject/concerto-analysis": "3.24.1",
    "@accordproject/concerto-linter": "3.24.1",
    "@accordproject/concerto-linter-default-ruleset": "3.24.1",
    "@accordproject/concerto-metamodel": "3.12.5",
    "@accordproject/markdown-it-cicero": "0.16.26",
}

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


def get_package_lock_json(repo_full_name):
    """指定リポジトリの package-lock.json を取得"""
    url = f"https://api.github.com/repos/{repo_full_name}/contents/package-lock.json"
    r = requests.get(url, headers=HEADERS)

    if r.status_code == 404:
        return None  # lockfile がない
    if r.status_code != 200:
        print(f"Error fetching {repo_full_name}: {r.text}")
        return None

    content = r.json().get("content")
    return json.loads(base64.b64decode(content).decode("utf-8"))


def scan_repo(repo):
    """package-lock.json を走査し、該当パッケージを返す"""
    repo_full_name = repo["full_name"]
    lock_json = get_package_lock_json(repo_full_name)

    if lock_json is None:
        return []

    found = []

    # dependencies に各パッケージが存在するか確認
    packages = lock_json.get("packages", {})

    for pkg_name, target_version in TARGET_PACKAGES.items():
        pkg_lock_entry = packages.get(f"node_modules/{pkg_name}")
        if pkg_lock_entry:
            version = pkg_lock_entry.get("version")
            if version == target_version:
                found.append((pkg_name, version))

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
        for repo, pkgs in result.items():
            print(f"\n📌 {repo}")
            for pkg, ver in pkgs:
                print(f"  - {pkg}@{ver}")


if __name__ == "__main__":
    main()
