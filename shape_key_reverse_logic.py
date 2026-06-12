"""逆シェイプキー変換で共有する純粋ロジックをまとめる。"""

from __future__ import annotations

from collections.abc import Sequence

Vector3 = tuple[float, float, float]


class ShapeKeyReverseError(ValueError):
    """逆シェイプキー作成に必要な前提が満たされないことを表す。"""


def validate_reverse_shape_key_inputs(
    source_name: str,
    target_name: str,
    result_name: str,
    source_vertex_count: int,
    target_vertex_count: int,
) -> None:
    """逆シェイプキー作成に使うキー名と頂点数を検証する。"""

    if not source_name:
        raise ShapeKeyReverseError("Source Shape Key を選択してください。")

    if not target_name:
        raise ShapeKeyReverseError("Target Shape Key を選択してください。")

    if source_name == target_name:
        raise ShapeKeyReverseError("Source と Target には別のキーを選択してください。")

    if not result_name.strip():
        raise ShapeKeyReverseError("Destination Shape Key の名前を入力してください。")

    if source_vertex_count <= 0 or target_vertex_count <= 0:
        raise ShapeKeyReverseError("頂点を持つメッシュのシェイプキーを選択してください。")

    if source_vertex_count != target_vertex_count:
        raise ShapeKeyReverseError("Source と Target の頂点数が一致していません。")


def build_reverse_shape_key_coordinates(target_coordinates: Sequence[Vector3]) -> list[Vector3]:
    """Target の座標列を、新規 Destination に書き込む座標列として返す。"""

    if not target_coordinates:
        raise ShapeKeyReverseError("Target Shape Key の頂点座標がありません。")

    # Destination は Source を相対基準にするため、絶対座標には Target の形状を入れる。
    return list(target_coordinates)
