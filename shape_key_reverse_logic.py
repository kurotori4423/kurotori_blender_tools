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
        raise ShapeKeyReverseError("戻し元シェイプキー A を選択してください。")

    if not target_name:
        raise ShapeKeyReverseError("戻し先シェイプキー B を選択してください。")

    if source_name == target_name:
        raise ShapeKeyReverseError("シェイプキー A と B には別のキーを選択してください。")

    if not result_name.strip():
        raise ShapeKeyReverseError("作成するシェイプキー C の名前を入力してください。")

    if source_vertex_count <= 0 or target_vertex_count <= 0:
        raise ShapeKeyReverseError("頂点を持つメッシュのシェイプキーを選択してください。")

    if source_vertex_count != target_vertex_count:
        raise ShapeKeyReverseError("シェイプキー A と B の頂点数が一致していません。")


def build_reverse_shape_key_coordinates(target_coordinates: Sequence[Vector3]) -> list[Vector3]:
    """戻し先 B の座標列を、新規シェイプキー C に書き込む座標列として返す。"""

    if not target_coordinates:
        raise ShapeKeyReverseError("戻し先シェイプキー B の頂点座標がありません。")

    # C は A を相対基準にするため、C 自体の絶対座標には到達先である B の形状を入れる。
    return list(target_coordinates)
