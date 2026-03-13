"""Kurotori Blender Tools アドオンのエントリーポイント。"""

import bpy

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


class KUROTORI_OT_show_message(bpy.types.Operator):
    """アドオンの読み込み確認用メッセージを表示する。"""

    bl_idname = "kurotori_tools.show_message"
    bl_label = "Show Message"
    bl_description = "アドオンが有効化されていることを確認します"

    def execute(self, context: bpy.types.Context) -> set[str]:
        """オペレーター実行時に Blender のステータスへ通知する。"""
        # 初期段階では最小の動作確認を優先し、依存の少ないレポート表示だけを行う。
        self.report({"INFO"}, "Kurotori Blender Tools is ready.")
        return {"FINISHED"}


class KUROTORI_PT_main_panel(bpy.types.Panel):
    """アドオンの最小 UI を 3D View に表示する。"""

    bl_label = "Kurotori Tools"
    bl_idname = "KUROTORI_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kurotori"

    def draw(self, context: bpy.types.Context) -> None:
        """有効化確認用のボタンを描画する。"""
        # 今後の機能追加先を明確にするため、最初から専用タブを確保しておく。
        layout = self.layout
        if layout is None:
            return

        layout.label(text="Addon loaded")
        layout.operator(KUROTORI_OT_show_message.bl_idname, icon="INFO")


CLASSES = (
    KUROTORI_OT_show_message,
    KUROTORI_PT_main_panel,
)


def register() -> None:
    """アドオンを Blender に登録する。"""
    # Blender の登録順序を固定し、将来ファイル分割しても追従しやすい構造を先に作る。
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """アドオンを Blender から解除する。"""
    # Blender の解除順序は登録と逆順にして、依存が増えた時の事故を避ける。
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
