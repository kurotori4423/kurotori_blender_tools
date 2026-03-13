"""ボーン整列ロジックの純粋関数を検証するテスト。"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

# アドオン本体の __init__.py を経由せず、純粋ロジックだけを直接テストできるようにする。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bone_align_logic import (  # noqa: E402
    BoneAlignmentError,
    build_aligned_segments,
    order_selected_bone_chain,
    project_bone_chain_joints_to_line,
)


@dataclass(eq=False)
class DummyBone:
    """親子関係だけを持つ簡易ボーンでチェーン検証を行う。"""

    name: str
    parent: "DummyBone | None" = None
    children: list["DummyBone"] = field(default_factory=list)


def _connect(parent: DummyBone, child: DummyBone) -> None:
    """親子関係を双方向に接続する。"""

    child.parent = parent
    parent.children.append(child)


def test_order_selected_bone_chain_returns_root_to_leaf_order() -> None:
    """単一路線の選択を根元から末端まで並べ替える。"""

    root = DummyBone("root")
    middle = DummyBone("middle")
    leaf = DummyBone("leaf")
    _connect(root, middle)
    _connect(middle, leaf)

    ordered = order_selected_bone_chain(
        [middle, leaf, root],
        lambda bone: bone.parent,
        lambda bone: bone.children,
    )

    assert [bone.name for bone in ordered] == ["root", "middle", "leaf"]


def test_order_selected_bone_chain_rejects_branch_selection() -> None:
    """分岐を含む選択は拒否する。"""

    root = DummyBone("root")
    branch = DummyBone("branch")
    left = DummyBone("left")
    right = DummyBone("right")
    _connect(root, branch)
    _connect(branch, left)
    _connect(branch, right)

    with pytest.raises(BoneAlignmentError):
        order_selected_bone_chain(
            [root, branch, left, right],
            lambda bone: bone.parent,
            lambda bone: bone.children,
        )


def test_project_bone_chain_joints_to_line_projects_three_bone_chain() -> None:
    """折れたチェーンの関節列を始点終点の直線上へ射影する。"""

    projected = project_bone_chain_joints_to_line(
        [
            (0.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (2.0, -1.0, 0.0),
            (3.0, 0.0, 0.0),
        ]
    )

    assert projected == pytest.approx(
        [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
        ]
    )


def test_project_bone_chain_joints_to_line_keeps_collinear_diagonal_chain() -> None:
    """既に同一直線上の関節列はほぼ変化しない。"""

    joint_positions = [
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0),
        (2.0, 2.0, 2.0),
        (3.0, 3.0, 3.0),
    ]

    assert project_bone_chain_joints_to_line(joint_positions) == pytest.approx(joint_positions)


def test_project_bone_chain_joints_to_line_supports_diagonal_reference_line() -> None:
    """基準線が斜めでも各関節が同一直線上へ並ぶ。"""

    projected = project_bone_chain_joints_to_line(
        [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (2.0, 1.0, 1.0),
            (3.0, 3.0, 3.0),
        ]
    )

    assert projected == pytest.approx(
        [
            (0.0, 0.0, 0.0),
            (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0),
            (4.0 / 3.0, 4.0 / 3.0, 4.0 / 3.0),
            (3.0, 3.0, 3.0),
        ]
    )


def test_project_bone_chain_joints_to_line_rejects_degenerate_line() -> None:
    """始点と終点が重なる場合は整列できない。"""

    with pytest.raises(BoneAlignmentError):
        project_bone_chain_joints_to_line(
            [
                (1.0, 1.0, 1.0),
                (2.0, 2.0, 2.0),
                (1.0, 1.0, 1.0),
            ]
        )


def test_build_aligned_segments_creates_continuous_head_tail_pairs() -> None:
    """関節列から連続するボーン区間を構築できる。"""

    assert build_aligned_segments(
        [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
        ]
    ) == [
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
        ((1.0, 0.0, 0.0), (2.0, 0.0, 0.0)),
    ]
