import os
import base64
import json
import requests
import yaml
from target_packages import TARGET_PACKAGES

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG = os.getenv("ORG")
TEAM_SLUG = os.getenv("TEAM_SLUG")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def get_team_repos():
    """Fetch all repositories under the specified team."""
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


def get_all_lockfile_paths(repo_full_name):
    """Recursively fetch all lockfile paths (package-lock.json, pnpm-lock.yaml) in the repository."""
    url = f"https://api.github.com/repos/{repo_full_name}/git/trees/HEAD?recursive=1"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"Error fetching tree for {repo_full_name}: {r.text}")
        return []
    tree = r.json().get("tree", [])
    return [
        item["path"]
        for item in tree
        if item["path"].endswith("package-lock.json")
        or item["path"].endswith("pnpm-lock.yaml")
    ]


def get_lockfile_content(repo_full_name, path):
    """Fetch and parse the lockfile from the specified repository and path."""
    url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        print(f"Error fetching {repo_full_name}:{path}: {r.text}")
        return None
    content = base64.b64decode(r.json().get("content")).decode("utf-8")
    if path.endswith("package-lock.json"):
        return json.loads(content)
    elif path.endswith("pnpm-lock.yaml"):
        return yaml.safe_load(content)
    return None


def scan_repo(repo):
    """Scan all lockfiles in the repository and return matched target packages."""
    repo_full_name = repo["full_name"]
    lock_paths = get_all_lockfile_paths(repo_full_name)
    found = []

    for path in lock_paths:
        lock_data = get_lockfile_content(repo_full_name, path)
        if lock_data is None:
            continue
        matched_pkgs = []
        if path.endswith("package-lock.json"):
            packages = lock_data.get("packages", {})
            for target in TARGET_PACKAGES:
                pkg_name = target["name"]
                target_version = target["version"]
                pkg_lock_entry = packages.get(f"node_modules/{pkg_name}")
                if pkg_lock_entry:
                    version = pkg_lock_entry.get("version")
                    if version == target_version:
                        matched_pkgs.append((pkg_name, version))
        elif path.endswith("pnpm-lock.yaml"):
            # pnpm-lock.yaml の場合は dependencies, devDependencies, optionalDependencies などを調べる
            import re

            pkgs_section = lock_data.get("packages", {})
            for target in TARGET_PACKAGES:
                pkg_name = target["name"]
                target_version = target["version"]
                # pnpm-lock.yaml の packages キーは "/pkg@version" の形式
                for key, val in pkgs_section.items():
                    # npm スコープ付きパッケージ対応
                    m = re.match(r"^/?(@?[^@]+/[^@]+|[^@]+)@(.+)$", key)
                    if m:
                        name, version = m.group(1), m.group(2)
                        if name == pkg_name and version == target_version:
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
