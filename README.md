# lockfile-vuln-checker

JavaScript プロジェクトの lockfile（`package-lock.json` や `pnpm-lock.yaml`）を走査し、指定した脆弱性パッケージが利用されていないかチェックするツールです。

## 特徴

- GitHub のチーム配下のリポジトリをスキャン
- lockfile 内の対象パッケージ（`target_packages.py` で指定可）を検出
- `package-lock.json` と `pnpm-lock.yaml` の両方に対応
- 子フォルダ内の lockfile も再帰的にスキャン

## セットアップ

1. [uv](https://github.com/astral-sh/uv) をインストール
2. プロジェクトディレクトリで以下を実行

```sh
uv sync
```

これで必要な Python パッケージがインストールされます。

## 使い方

1. `.env.example` をコピーして `.env` を作成し、必要な環境変数を設定してください

   - `GITHUB_TOKEN` : GitHub のアクセストークン
   - `ORG` : GitHub 組織名
   - `TEAM_SLUG` : チームのスラッグ

2. スクリプトを実行

```sh
python main.py
```

## 出力例

```
Fetching team repositories...

Scanning org/repo1...
Scanning org/repo2...

=== Scan Result ===

📌 org/repo1
  - Found in: path/to/package-lock.json
    - lodash@4.17.21
```
