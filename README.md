# lockfile-vuln-checker

This tool scans JavaScript project lockfiles (`package-lock.json` and `pnpm-lock.yaml`) to check if specified vulnerable packages are being used.

## Features

- Scans repositories under a GitHub team
- Detects target packages specified in `target_packages.py` within lockfiles
- Supports both `package-lock.json` and `pnpm-lock.yaml`
- Recursively scans lockfiles in subfolders

## Setup

1. Install [uv](https://github.com/astral-sh/uv)
2. Run the following in your project directory:

```sh
uv sync
```

This will install the required Python packages.

## Usage

1. Copy `.env.example` to `.env` and set the required environment variables:

   - `GITHUB_TOKEN`: GitHub access token
   - `ORG`: GitHub organization name
   - `TEAM_SLUG`: Team slug

2. Run the script:

```sh
python main.py
```

## Example Output

```
Fetching team repositories...

Scanning org/repo1...
Scanning org/repo2...

=== Scan Result ===

📌 org/repo1
  - Found in: path/to/package-lock.json
    - lodash@4.17.21
```
