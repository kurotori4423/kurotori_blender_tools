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

このリポジトリでは、Blender 本体とは別に `uv venv` を使った Python 仮想環境を用意して、補完や静的解析を行う想定です。

```powershell
cd D:\Apps\blender-scripts\addons\kurotori_blender_tools
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install fake-bpy-module-latest ruff basedpyright pytest
```

`fake-bpy-module` は Blender 外でのエディタ補完や型補助のために使います。  
初回は `pyproject.toml` を置かず、必要な依存は上記のように仮想環境へ導入する運用にします。将来的に依存を固定化する段階で、`uv + pyproject optional-dependencies` に移行する想定です。

## あると便利なツール

- `uv`: 仮想環境作成と依存導入の入口
- `fake-bpy-module`: Blender API の補完と静的解析補助
- `ruff`: lint / format
- `basedpyright` または `pyright`: 型チェック補助
- `pytest`: Blender 非依存ロジックのテスト
- `VS Code` または `PyCharm`: 編集、補完、デバッグ
- `just` または `Taskfile`: 開発コマンドの定型化

## 今後の方針

- 機能追加時は `__init__.py` を起点に段階的に構成を分割します。
- Blender API に依存しない処理は、可能な限りテストしやすい形で分離します。
- 機能一覧と使用方法は、実装に合わせて README を更新します。
