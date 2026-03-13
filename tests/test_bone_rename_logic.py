"""ボーン連番リネームの純粋ロジックを検証するテスト。"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

# アドオン本体の __init__.py を経由せず、純粋ロジックだけを直接テストできるようにする。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bone_rename_logic import collect_linear_chain, format_bone_name


@dataclass
class DummyBone:
    """子関係だけを持つ簡易ボーンで停止条件を検証する。"""

    name: str
    children: list["DummyBone"] = field(default_factory=list)


def test_format_bone_name_with_side() -> None:
    """左右指定ありの命名規則を確認する。"""

    assert format_bone_name("Arm", 1, "L") == "Arm_001_L"


def test_format_bone_name_without_side() -> None:
    """左右指定なしでは余分な区切りを付けないことを確認する。"""

    assert format_bone_name("Spine", 12, "NONE") == "Spine_012"


def test_collect_linear_chain_stops_at_leaf() -> None:
    """子が 1 本ずつ続く場合は末端まで収集する。"""

    leaf = DummyBone("leaf")
    middle = DummyBone("middle", children=[leaf])
    root = DummyBone("root", children=[middle])

    chain = collect_linear_chain(root, lambda bone: bone.children)

    assert [bone.name for bone in chain] == ["root", "middle", "leaf"]


def test_collect_linear_chain_includes_branch_node_then_stops() -> None:
    """分岐点のボーンを含めて停止することを確認する。"""

    branch = DummyBone("branch", children=[DummyBone("left"), DummyBone("right")])
    root = DummyBone("root", children=[branch])

    chain = collect_linear_chain(root, lambda bone: bone.children)

    assert [bone.name for bone in chain] == ["root", "branch"]
