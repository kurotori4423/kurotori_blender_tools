"""ボーン連番リネームで共有する純粋ロジックをまとめる。"""

from collections.abc import Callable, Sequence
from typing import TypeVar

BoneNode = TypeVar("BoneNode")


def format_bone_name(part_name: str, index: int, side: str) -> str:
    """部位名、連番、左右指定から最終的なボーン名を組み立てる。"""

    base_name = f"{part_name}_{index:03d}"
    if side == "NONE":
        return base_name
    return f"{base_name}_{side}"


def collect_linear_chain(
    start_bone: BoneNode, child_getter: Callable[[BoneNode], Sequence[BoneNode]]
) -> list[BoneNode]:
    """分岐する手前までの直線チェーンを開始ボーンから収集する。"""

    chain: list[BoneNode] = []
    current_bone = start_bone

    while True:
        chain.append(current_bone)

        # 分岐元のボーン自体は対象に含めたいので、子数判定は追加後に行う。
        children = list(child_getter(current_bone))
        if len(children) != 1:
            return chain

        current_bone = children[0]
