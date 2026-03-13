"""Kurotori Blender Tools アドオンのエントリーポイント。"""

bl_info = {
    "name": "Kurotori Blender Tools",
    "author": "kurotori",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D",
    "description": "個人用の Blender ユーティリティをまとめるアドオンです。",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}


def register() -> None:
    """アドオンを Blender に登録する。"""
    # 初期段階では登録対象クラスを持たず、将来の機能追加時にここへ登録処理を集約する。
    return None


def unregister() -> None:
    """アドオンを Blender から解除する。"""
    # register() と対になる解除処理の置き場所を先に固定し、拡張時の実装位置を明確にする。
    return None
