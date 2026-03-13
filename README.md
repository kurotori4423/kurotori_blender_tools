# Kurotori Blender Tools

個人用の Blender 便利機能をまとめるためのアドオンリポジトリです。  
このリポジトリは `blender-scripts/addons/kurotori_blender_tools` 配下に配置し、Blender 側で `blender-scripts` を scripts directory として認識させる前提で運用します。

## ディレクトリ構成

```text
blender-scripts/
└─ addons/
   └─ kurotori_blender_tools/
      ├─ __init__.py
      ├─ README.md
      └─ AGENTS.md
```

`kurotori_blender_tools` フォルダ自体が Blender アドオンとして認識されます。

## 機能一覧

現時点では初期セットアップのみです。  
今後は機能追加のたびに、以下の形式で追記します。

- 機能名
- 概要
- 使用方法
- 制約や注意点

## 使用方法

1. Blender の設定で `D:\Apps\blender-scripts` を scripts directory として登録します。
2. Blender を再起動するか、アドオン一覧を再読込します。
3. `Edit > Preferences > Add-ons` を開き、`Kurotori Blender Tools` を検索します。
4. アドオンを有効化します。

## 開発環境セットアップ

このリポジトリでは、Blender 本体とは別に `uv venv` を使った Python 仮想環境を用意して、補完や静的解析を行います。  
依存は `pyproject.toml` と `uv.lock` で管理します。

```powershell
cd D:\Apps\blender-scripts\addons\kurotori_blender_tools
uv sync --extra dev
.\.venv\Scripts\Activate.ps1
```

`uv sync --extra dev` により、`.venv` の作成と開発依存の導入をまとめて再現できます。  
`fake-bpy-module` は Blender 外での補完や型補助のために使い、`ruff`、`basedpyright`、`pytest` は CLI ツールとして利用します。

### よく使うコマンド

```powershell
uv run ruff check .
uv run basedpyright
uv run pytest
```

## 導入済みの開発ツール

- `uv`: 仮想環境作成、依存同期、CLI 実行の入口
- `fake-bpy-module`: Blender API の補完と静的解析補助
- `ruff`: lint / format
- `basedpyright`: 型チェック補助
- `pytest`: Blender 非依存ロジックのテスト

必要に応じて、将来的に `just` や `Taskfile` のようなコマンド定型化ツールを追加できます。

## 今後の方針

- 機能追加時は `__init__.py` を起点に段階的に構成を分割します。
- Blender API に依存しない処理は、可能な限りテストしやすい形で分離します。
- 機能一覧と使用方法は、実装に合わせて README を更新します。
