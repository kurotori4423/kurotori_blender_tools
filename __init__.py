"""Kurotori Blender Tools アドオンのエントリーポイント。"""

import bpy

from .bone_rename_logic import collect_linear_chain, format_bone_name

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


if hasattr(bpy, "types"):

    class KUROTORI_PG_bone_rename_settings(bpy.types.PropertyGroup):
        """ボーン連番リネームの UI 設定を保持する。"""

        # 実行前にユーザーが調整する一時設定なので、
        # 保存データへの影響が小さい WindowManager に寄せる。
        part_name: bpy.props.StringProperty(  # type: ignore[valid-type]
            name="部位名",
            description="リネーム後の先頭に付ける部位名",
            default="Bone",
        )
        start_index: bpy.props.IntProperty(  # type: ignore[valid-type]
            name="開始番号",
            description="最初のボーンに付ける連番",
            default=1,
            min=1,
            soft_min=1,
        )
        side: bpy.props.EnumProperty(  # type: ignore[valid-type]
            name="左右",
            description="名前の末尾に付ける左右識別子",
            items=(
                ("NONE", "なし", "左右識別子を付けません"),
                ("L", "L", "左側のボーンとして命名します"),
                ("R", "R", "右側のボーンとして命名します"),
            ),
            default="NONE",
        )


    def _get_bone_rename_settings(
        context: bpy.types.Context,
    ) -> KUROTORI_PG_bone_rename_settings | None:
        """WindowManager に登録したリネーム設定を安全に取得する。"""

        window_manager = context.window_manager
        if window_manager is None:
            return None

        settings = getattr(window_manager, "kurotori_bone_rename_settings", None)
        if settings is None or not isinstance(settings, KUROTORI_PG_bone_rename_settings):
            return None

        return settings


    def _validate_bone_rename_context(
        context: bpy.types.Context,
    ) -> tuple[bpy.types.Object | None, bpy.types.Armature | None, bpy.types.EditBone | None]:
        """リネーム実行に必要な Blender コンテキストをまとめて検証する。"""

        active_object = context.active_object
        if active_object is None:
            return None, None, None

        if active_object.type != "ARMATURE" or context.mode != "EDIT_ARMATURE":
            return active_object, None, None

        armature_data = active_object.data
        if not isinstance(armature_data, bpy.types.Armature):
            return active_object, None, None

        active_bone = armature_data.edit_bones.active
        if active_bone is None:
            return active_object, armature_data, None

        return active_object, armature_data, active_bone


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


    class KUROTORI_OT_rename_bone_chain(bpy.types.Operator):
        """アクティブボーンから直線の子チェーンを連番でリネームする。"""

        bl_idname = "kurotori_tools.rename_bone_chain"
        bl_label = "Rename Bone Chain"
        bl_description = "アクティブボーンから子方向へ連番リネームします"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context: bpy.types.Context) -> set[str]:
            """現在の編集状態を検証しつつ、対象チェーンを順にリネームする。"""

            settings = _get_bone_rename_settings(context)
            if settings is None:
                self.report({"ERROR"}, "ボーンリネーム設定を取得できませんでした。")
                return {"CANCELLED"}

            part_name = settings.part_name.strip()
            if not part_name:
                self.report({"ERROR"}, "部位名を入力してください。")
                return {"CANCELLED"}

            active_object, armature_data, active_bone = _validate_bone_rename_context(context)
            if active_object is None:
                self.report({"ERROR"}, "アクティブオブジェクトが見つかりません。")
                return {"CANCELLED"}

            if armature_data is None:
                self.report({"ERROR"}, "Armature の Edit Mode で実行してください。")
                return {"CANCELLED"}

            if active_bone is None:
                self.report({"ERROR"}, "開始点となるアクティブボーンを選択してください。")
                return {"CANCELLED"}

            target_chain = collect_linear_chain(active_bone, lambda bone: tuple(bone.children))
            for offset, bone in enumerate(target_chain):
                # Blender の重複名解決は内部挙動に任せ、ここでは一貫した命名規則だけを保証する。
                bone.name = format_bone_name(
                    part_name,
                    settings.start_index + offset,
                    settings.side,
                )

            self.report({"INFO"}, f"{len(target_chain)} 本のボーンをリネームしました。")
            return {"FINISHED"}


    class KUROTORI_PT_main_panel(bpy.types.Panel):
        """アドオンの主要 UI を 3D View に表示する。"""

        bl_label = "Kurotori Tools"
        bl_idname = "KUROTORI_PT_main_panel"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Kurotori"

        def draw(self, context: bpy.types.Context) -> None:
            """確認用 UI とボーン連番リネーム UI を描画する。"""
            # 将来の機能追加でも配置を見失わないよう、用途ごとに UI ブロックを分ける。
            layout = self.layout
            if layout is None:
                return

            settings = _get_bone_rename_settings(context)

            layout.label(text="Addon loaded")
            layout.operator(KUROTORI_OT_show_message.bl_idname, icon="INFO")

            box = layout.box()
            box.label(text="Bone Rename Chain", icon="BONE_DATA")
            if settings is None:
                box.label(text="設定を読み込めませんでした。", icon="ERROR")
                return

            box.prop(settings, "part_name")
            box.prop(settings, "start_index")
            box.prop(settings, "side")
            box.operator(KUROTORI_OT_rename_bone_chain.bl_idname, icon="GREASEPENCIL")


    CLASSES = (
        KUROTORI_PG_bone_rename_settings,
        KUROTORI_OT_show_message,
        KUROTORI_OT_rename_bone_chain,
        KUROTORI_PT_main_panel,
    )


    def register() -> None:
        """アドオンを Blender に登録する。"""
        # Blender の登録順序を固定し、将来ファイル分割しても追従しやすい構造を先に作る。
        for cls in CLASSES:
            bpy.utils.register_class(cls)

        bpy.types.WindowManager.kurotori_bone_rename_settings = bpy.props.PointerProperty(  # type: ignore[attr-defined]
            type=KUROTORI_PG_bone_rename_settings
        )


    def unregister() -> None:
        """アドオンを Blender から解除する。"""
        if hasattr(bpy.types.WindowManager, "kurotori_bone_rename_settings"):
            del bpy.types.WindowManager.kurotori_bone_rename_settings  # type: ignore[attr-defined]

        # Blender の解除順序は登録と逆順にして、依存が増えた時の事故を避ける。
        for cls in reversed(CLASSES):
            bpy.utils.unregister_class(cls)

else:

    def register() -> None:
        """CLI テスト環境では Blender 登録処理を行わない。"""


    def unregister() -> None:
        """CLI テスト環境では Blender 解除処理を行わない。"""
