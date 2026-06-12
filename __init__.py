"""Kurotori Blender Tools アドオンのエントリーポイント。"""

from typing import Any

import bpy

from .bone_align_logic import (
    BoneAlignmentError,
    build_aligned_segments,
    order_selected_bone_chain,
    project_bone_chain_joints_to_line,
)
from .bone_rename_logic import collect_linear_chain, format_bone_name
from .shape_key_reverse_logic import (
    ShapeKeyReverseError,
    build_reverse_shape_key_coordinates,
    validate_reverse_shape_key_inputs,
)

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
    _SHAPE_KEY_SOURCE_ITEMS: list[tuple[str, str, str]] = []
    _SHAPE_KEY_TARGET_ITEMS: list[tuple[str, str, str]] = []

    def _empty_shape_key_items() -> list[tuple[str, str, str]]:
        """EnumProperty が空にならないよう、未選択用の項目を返す。"""

        return [("", "未選択", "対象メッシュのシェイプキーを選択してください")]


    def _get_shape_key_items(
        context: bpy.types.Context | None, *, include_basis: bool
    ) -> list[tuple[str, str, str]]:
        """アクティブ Mesh のシェイプキーを UI 選択肢へ変換する。"""

        global _SHAPE_KEY_SOURCE_ITEMS, _SHAPE_KEY_TARGET_ITEMS

        if context is None:
            items = _empty_shape_key_items()
            if include_basis:
                _SHAPE_KEY_TARGET_ITEMS = items
                return _SHAPE_KEY_TARGET_ITEMS
            _SHAPE_KEY_SOURCE_ITEMS = items
            return _SHAPE_KEY_SOURCE_ITEMS

        active_object = context.active_object
        if active_object is None or active_object.type != "MESH":
            items = _empty_shape_key_items()
            if include_basis:
                _SHAPE_KEY_TARGET_ITEMS = items
                return _SHAPE_KEY_TARGET_ITEMS
            _SHAPE_KEY_SOURCE_ITEMS = items
            return _SHAPE_KEY_SOURCE_ITEMS

        mesh_data = active_object.data
        if not isinstance(mesh_data, bpy.types.Mesh):
            items = _empty_shape_key_items()
            if include_basis:
                _SHAPE_KEY_TARGET_ITEMS = items
                return _SHAPE_KEY_TARGET_ITEMS
            _SHAPE_KEY_SOURCE_ITEMS = items
            return _SHAPE_KEY_SOURCE_ITEMS

        shape_keys = mesh_data.shape_keys
        if shape_keys is None:
            items = _empty_shape_key_items()
            if include_basis:
                _SHAPE_KEY_TARGET_ITEMS = items
                return _SHAPE_KEY_TARGET_ITEMS
            _SHAPE_KEY_SOURCE_ITEMS = items
            return _SHAPE_KEY_SOURCE_ITEMS

        reference_key = shape_keys.reference_key
        items: list[tuple[str, str, str]] = []
        for key_block in shape_keys.key_blocks:
            if not include_basis and key_block == reference_key:
                continue
            items.append((key_block.name, key_block.name, ""))

        # Blender の動的 EnumProperty は返却した文字列参照を保持しないことがある。
        # 日本語名の表示崩れを避けるため、項目リストをモジュール内に保持して返す。
        if include_basis:
            _SHAPE_KEY_TARGET_ITEMS = items or _empty_shape_key_items()
            return _SHAPE_KEY_TARGET_ITEMS

        _SHAPE_KEY_SOURCE_ITEMS = items or _empty_shape_key_items()
        return _SHAPE_KEY_SOURCE_ITEMS


    def _source_shape_key_items(
        self: Any, context: bpy.types.Context | None
    ) -> list[tuple[str, str, str]]:
        """戻し元 A の選択肢を返す。"""

        # A は変形済み状態を表すため、基準形状である Basis は候補から外す。
        return _get_shape_key_items(context, include_basis=False)


    def _target_shape_key_items(
        self: Any, context: bpy.types.Context | None
    ) -> list[tuple[str, str, str]]:
        """戻し先 B の選択肢を返す。"""

        return _get_shape_key_items(context, include_basis=True)

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


    class KUROTORI_PG_shape_key_reverse_settings(bpy.types.PropertyGroup):
        """逆シェイプキー変換の UI 設定を保持する。"""

        # 対象はアクティブ Mesh によって変わるため、EnumProperty は描画時に候補を作る。
        source_shape_key: bpy.props.EnumProperty(  # type: ignore[valid-type]
            name="シェイプキー A",
            description="戻し元になる変形シェイプキー",
            items=_source_shape_key_items,
        )
        target_shape_key: bpy.props.EnumProperty(  # type: ignore[valid-type]
            name="シェイプキー B",
            description="戻し先になるシェイプキー。Basis も選択できます",
            items=_target_shape_key_items,
        )
        result_shape_key_name: bpy.props.StringProperty(  # type: ignore[valid-type]
            name="シェイプキー C",
            description="作成する逆シェイプキー名",
            default="Reverse",
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


    def _get_shape_key_reverse_settings(
        context: bpy.types.Context,
    ) -> KUROTORI_PG_shape_key_reverse_settings | None:
        """WindowManager に登録した逆シェイプキー設定を安全に取得する。"""

        window_manager = context.window_manager
        if window_manager is None:
            return None

        settings = getattr(window_manager, "kurotori_shape_key_reverse_settings", None)
        if settings is None or not isinstance(settings, KUROTORI_PG_shape_key_reverse_settings):
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


    def _get_selected_edit_bones(armature_data: bpy.types.Armature) -> list[bpy.types.EditBone]:
        """Edit Mode で選択されているボーンだけを取得する。"""

        # Blender の選択状態を都度読み直し、アクティブ依存の暗黙挙動を避ける。
        return [bone for bone in armature_data.edit_bones if bone.select]


    def _vector_to_tuple(vector: Any) -> tuple[float, float, float]:
        """Blender のベクトル互換値を純粋ロジック向けのタプルへ変換する。"""

        return (float(vector[0]), float(vector[1]), float(vector[2]))


    def _get_active_mesh_shape_keys(
        context: bpy.types.Context,
    ) -> tuple[bpy.types.Object | None, bpy.types.Mesh | None, bpy.types.Key | None]:
        """逆シェイプキー作成に必要な Mesh と ShapeKeys を取得する。"""

        active_object = context.active_object
        if active_object is None:
            return None, None, None

        if active_object.type != "MESH":
            return active_object, None, None

        mesh_data = active_object.data
        if not isinstance(mesh_data, bpy.types.Mesh):
            return active_object, None, None

        shape_keys = mesh_data.shape_keys
        if shape_keys is None:
            return active_object, mesh_data, None

        return active_object, mesh_data, shape_keys


    def _shape_key_coordinates(
        key_block: bpy.types.ShapeKey,
    ) -> list[tuple[float, float, float]]:
        """Blender のシェイプキー座標を純粋ロジック向けのタプル列へ変換する。"""

        coordinates: list[tuple[float, float, float]] = []
        for point in key_block.data:
            # fake-bpy-module では ShapeKeyPoint の co 型が解決されないため、境界で Any に寄せる。
            shape_key_point: Any = point
            coordinates.append(_vector_to_tuple(shape_key_point.co))

        return coordinates


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


    class KUROTORI_OT_align_bone_chain_linear(bpy.types.Operator):
        """選択ボーンチェーンを根元 Head と末端 Tail の直線上へ整列する。"""

        bl_idname = "kurotori_tools.align_bone_chain_linear"
        bl_label = "Align Bone Chain"
        bl_description = "選択したボーンチェーンを始点と終点の直線上へ整列します"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context: bpy.types.Context) -> set[str]:
            """選択チェーンを検証し、各関節を基準直線へ射影して再配置する。"""

            active_object, armature_data, _active_bone = _validate_bone_rename_context(context)
            if active_object is None:
                self.report({"ERROR"}, "アクティブオブジェクトが見つかりません。")
                return {"CANCELLED"}

            if armature_data is None:
                self.report({"ERROR"}, "Armature の Edit Mode で実行してください。")
                return {"CANCELLED"}

            selected_bones = _get_selected_edit_bones(armature_data)

            try:
                ordered_chain = order_selected_bone_chain(
                    selected_bones,
                    lambda bone: bone.parent,
                    lambda bone: tuple(bone.children),
                )
                joint_positions = [_vector_to_tuple(ordered_chain[0].head)]
                joint_positions.extend(_vector_to_tuple(bone.tail) for bone in ordered_chain)
                aligned_segments = build_aligned_segments(
                    project_bone_chain_joints_to_line(joint_positions)
                )
            except BoneAlignmentError as error:
                self.report({"ERROR"}, str(error))
                return {"CANCELLED"}

            for bone, (new_head, new_tail) in zip(ordered_chain, aligned_segments, strict=True):
                bone.head = new_head
                bone.tail = new_tail

            self.report({"INFO"}, f"{len(ordered_chain)} 本のボーンを整列しました。")
            return {"FINISHED"}


    class KUROTORI_OT_create_reverse_shape_key(bpy.types.Operator):
        """A から B へ戻すための相対シェイプキー C を新規作成する。"""

        bl_idname = "kurotori_tools.create_reverse_shape_key"
        bl_label = "Create Reverse Shape Key"
        bl_description = "シェイプキー A から B へ変化する相対シェイプキーを作成します"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context: bpy.types.Context) -> set[str]:
            """選択された A/B の関係から新規シェイプキー C を作成する。"""

            settings = _get_shape_key_reverse_settings(context)
            if settings is None:
                self.report({"ERROR"}, "逆シェイプキー設定を取得できませんでした。")
                return {"CANCELLED"}

            active_object, _mesh_data, shape_keys = _get_active_mesh_shape_keys(context)
            if active_object is None:
                self.report({"ERROR"}, "アクティブオブジェクトが見つかりません。")
                return {"CANCELLED"}

            if shape_keys is None:
                self.report({"ERROR"}, "シェイプキーを持つ Mesh オブジェクトを選択してください。")
                return {"CANCELLED"}

            source_key = shape_keys.key_blocks.get(settings.source_shape_key)
            target_key = shape_keys.key_blocks.get(settings.target_shape_key)
            if source_key is None or target_key is None:
                self.report({"ERROR"}, "シェイプキー A または B を選択してください。")
                return {"CANCELLED"}

            result_name = settings.result_shape_key_name.strip()
            try:
                validate_reverse_shape_key_inputs(
                    source_key.name,
                    target_key.name,
                    result_name,
                    len(source_key.data),
                    len(target_key.data),
                )
                reverse_coordinates = build_reverse_shape_key_coordinates(
                    _shape_key_coordinates(target_key)
                )
            except ShapeKeyReverseError as error:
                self.report({"ERROR"}, str(error))
                return {"CANCELLED"}

            new_shape_key = active_object.shape_key_add(name=result_name, from_mix=False)
            new_shape_key.relative_key = source_key
            for point, coordinate in zip(new_shape_key.data, reverse_coordinates, strict=True):
                # fake-bpy-module では co 型が解決されないため、境界で Any に寄せる。
                shape_key_point: Any = point
                shape_key_point.co = coordinate

            active_object.active_shape_key_index = shape_keys.key_blocks.find(new_shape_key.name)

            self.report({"INFO"}, f"逆シェイプキー {new_shape_key.name} を作成しました。")
            return {"FINISHED"}


    class KUROTORI_PT_main_panel(bpy.types.Panel):
        """アドオンの主要 UI を 3D View に表示する。"""

        bl_label = "Kurotori Tools"
        bl_idname = "KUROTORI_PT_main_panel"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Kurotori"

        def draw(self, context: bpy.types.Context) -> None:
            """確認用 UI と各ツールの設定 UI を描画する。"""
            # 将来の機能追加でも配置を見失わないよう、用途ごとに UI ブロックを分ける。
            layout = self.layout
            if layout is None:
                return

            bone_rename_settings = _get_bone_rename_settings(context)
            shape_key_reverse_settings = _get_shape_key_reverse_settings(context)

            layout.label(text="Addon loaded")
            layout.operator(KUROTORI_OT_show_message.bl_idname, icon="INFO")

            box = layout.box()
            box.label(text="Bone Rename Chain", icon="BONE_DATA")
            if bone_rename_settings is None:
                box.label(text="設定を読み込めませんでした。", icon="ERROR")
                return

            box.prop(bone_rename_settings, "part_name")
            box.prop(bone_rename_settings, "start_index")
            box.prop(bone_rename_settings, "side")
            box.operator(KUROTORI_OT_rename_bone_chain.bl_idname, icon="GREASEPENCIL")

            align_box = layout.box()
            align_box.label(text="Bone Align Chain", icon="CON_TRACKTO")
            align_box.label(text="選択した単一路線のボーンを直線へ整列します。")
            align_box.operator(
                KUROTORI_OT_align_bone_chain_linear.bl_idname,
                icon="DRIVER_DISTANCE",
            )

            shape_key_box = layout.box()
            shape_key_box.label(text="Reverse Shape Key", icon="SHAPEKEY_DATA")
            if shape_key_reverse_settings is None:
                shape_key_box.label(text="設定を読み込めませんでした。", icon="ERROR")
                return

            shape_key_box.prop(shape_key_reverse_settings, "source_shape_key")
            shape_key_box.prop(shape_key_reverse_settings, "target_shape_key")
            shape_key_box.prop(shape_key_reverse_settings, "result_shape_key_name")
            shape_key_box.operator(
                KUROTORI_OT_create_reverse_shape_key.bl_idname,
                icon="ADD",
            )


    CLASSES = (
        KUROTORI_PG_bone_rename_settings,
        KUROTORI_PG_shape_key_reverse_settings,
        KUROTORI_OT_show_message,
        KUROTORI_OT_rename_bone_chain,
        KUROTORI_OT_align_bone_chain_linear,
        KUROTORI_OT_create_reverse_shape_key,
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
        bpy.types.WindowManager.kurotori_shape_key_reverse_settings = bpy.props.PointerProperty(  # type: ignore[attr-defined]
            type=KUROTORI_PG_shape_key_reverse_settings
        )


    def unregister() -> None:
        """アドオンを Blender から解除する。"""
        if hasattr(bpy.types.WindowManager, "kurotori_bone_rename_settings"):
            del bpy.types.WindowManager.kurotori_bone_rename_settings  # type: ignore[attr-defined]
        if hasattr(bpy.types.WindowManager, "kurotori_shape_key_reverse_settings"):
            del bpy.types.WindowManager.kurotori_shape_key_reverse_settings  # type: ignore[attr-defined]

        # Blender の解除順序は登録と逆順にして、依存が増えた時の事故を避ける。
        for cls in reversed(CLASSES):
            bpy.utils.unregister_class(cls)

else:

    def register() -> None:
        """CLI テスト環境では Blender 登録処理を行わない。"""


    def unregister() -> None:
        """CLI テスト環境では Blender 解除処理を行わない。"""
