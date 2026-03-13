"""ボーン整列機能で共有する純粋ロジックをまとめる。"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

BoneNode = TypeVar("BoneNode")
Vector3 = tuple[float, float, float]


class BoneAlignmentError(ValueError):
    """ボーン整列に必要な前提が満たされないことを表す。"""


def _vector_subtract(left: Vector3, right: Vector3) -> Vector3:
    """2 点の差分ベクトルを返す。"""

    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def _vector_add(left: Vector3, right: Vector3) -> Vector3:
    """2 つのベクトルを加算する。"""

    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def _vector_scale(vector: Vector3, factor: float) -> Vector3:
    """ベクトルをスカラー倍する。"""

    return (vector[0] * factor, vector[1] * factor, vector[2] * factor)


def _dot_product(left: Vector3, right: Vector3) -> float:
    """3 次元ベクトルの内積を返す。"""

    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def _squared_length(vector: Vector3) -> float:
    """長さ比較に使う二乗ノルムを返す。"""

    return _dot_product(vector, vector)


def order_selected_bone_chain(
    selected_bones: Iterable[BoneNode],
    parent_getter: Callable[[BoneNode], BoneNode | None],
    child_getter: Callable[[BoneNode], Sequence[BoneNode]],
) -> list[BoneNode]:
    """選択ボーン集合を根元から末端までの単一路線チェーンへ並べ替える。"""

    chain_candidates = list(selected_bones)
    if not chain_candidates:
        raise BoneAlignmentError("ボーンが選択されていません。")

    selected_lookup = set(chain_candidates)
    parent_map: dict[BoneNode, BoneNode | None] = {}
    child_map: dict[BoneNode, list[BoneNode]] = {}

    for bone in chain_candidates:
        parent = parent_getter(bone)
        selected_parent = parent if parent in selected_lookup else None
        selected_children = [child for child in child_getter(bone) if child in selected_lookup]

        if len(selected_children) > 1:
            raise BoneAlignmentError("分岐を含む選択は整列できません。")

        parent_map[bone] = selected_parent
        child_map[bone] = selected_children

    roots = [bone for bone in chain_candidates if parent_map[bone] is None]
    leaves = [bone for bone in chain_candidates if len(child_map[bone]) == 0]

    if len(roots) != 1 or len(leaves) != 1:
        # 複数島や循環を早期に弾き、Blender 側で不自然な部分整列を起こさない。
        raise BoneAlignmentError("選択ボーンは根元と末端が一意な単一路線である必要があります。")

    ordered_chain: list[BoneNode] = []
    current_bone = roots[0]
    visited: set[BoneNode] = set()

    while True:
        if current_bone in visited:
            raise BoneAlignmentError("循環を含む選択は整列できません。")

        visited.add(current_bone)
        ordered_chain.append(current_bone)

        next_children = child_map[current_bone]
        if not next_children:
            break

        current_bone = next_children[0]

    if len(ordered_chain) != len(chain_candidates):
        raise BoneAlignmentError("複数の独立した選択チェーンは同時に整列できません。")

    return ordered_chain


def project_point_onto_line(point: Vector3, line_start: Vector3, line_end: Vector3) -> Vector3:
    """点を line_start から line_end へ伸びる直線へ正射影する。"""

    line_direction = _vector_subtract(line_end, line_start)
    direction_length_squared = _squared_length(line_direction)
    if direction_length_squared <= 1.0e-12:
        raise BoneAlignmentError("根元 Head と末端 Tail が近すぎて基準直線を定義できません。")

    point_offset = _vector_subtract(point, line_start)
    projection_factor = _dot_product(point_offset, line_direction) / direction_length_squared
    return _vector_add(line_start, _vector_scale(line_direction, projection_factor))


def project_bone_chain_joints_to_line(joint_positions: Sequence[Vector3]) -> list[Vector3]:
    """関節列を始点と終点で定義した直線へ射影した新しい関節列を返す。"""

    if len(joint_positions) < 2:
        raise BoneAlignmentError("整列には少なくとも 1 本のボーンが必要です。")

    line_start = joint_positions[0]
    line_end = joint_positions[-1]
    return [project_point_onto_line(point, line_start, line_end) for point in joint_positions]


def build_aligned_segments(joint_positions: Sequence[Vector3]) -> list[tuple[Vector3, Vector3]]:
    """射影済みの関節列から各ボーンの Head/Tail ペアを構築する。"""

    if len(joint_positions) < 2:
        raise BoneAlignmentError("整列後の関節列が不足しています。")

    return [
        (joint_positions[index], joint_positions[index + 1])
        for index in range(len(joint_positions) - 1)
    ]
