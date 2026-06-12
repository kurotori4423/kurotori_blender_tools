"""逆シェイプキー変換ロジックの純粋関数を検証するテスト。"""

import sys
from pathlib import Path

import pytest

# アドオン本体の __init__.py を経由せず、純粋ロジックだけを直接テストできるようにする。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shape_key_reverse_logic import (  # noqa: E402
    ShapeKeyReverseError,
    build_reverse_shape_key_coordinates,
    validate_reverse_shape_key_inputs,
)


def test_validate_reverse_shape_key_inputs_rejects_same_shape_key() -> None:
    """Source と Target が同じシェイプキーの場合は差分作成を拒否する。"""

    with pytest.raises(ShapeKeyReverseError):
        validate_reverse_shape_key_inputs("Smile", "Smile", "Smile_Reset", 3, 3)


def test_validate_reverse_shape_key_inputs_rejects_blank_result_name() -> None:
    """作成先名が空白だけの場合はシェイプキーを作らない。"""

    with pytest.raises(ShapeKeyReverseError):
        validate_reverse_shape_key_inputs("Smile", "Basis", "   ", 3, 3)


def test_validate_reverse_shape_key_inputs_rejects_zero_vertices() -> None:
    """頂点を持たないキーは変換対象にしない。"""

    with pytest.raises(ShapeKeyReverseError):
        validate_reverse_shape_key_inputs("Smile", "Basis", "Smile_Reset", 0, 0)


def test_validate_reverse_shape_key_inputs_rejects_mismatched_vertex_count() -> None:
    """Source と Target の頂点数が違う場合は座標コピーを拒否する。"""

    with pytest.raises(ShapeKeyReverseError):
        validate_reverse_shape_key_inputs("Smile", "Basis", "Smile_Reset", 3, 2)


def test_build_reverse_shape_key_coordinates_uses_target_shape_key_coordinates() -> None:
    """通常 Target の座標を Destination の座標として使う。"""

    target_coordinates = [(0.0, 0.0, 0.0), (1.0, 2.0, 3.0)]

    assert build_reverse_shape_key_coordinates(target_coordinates) == target_coordinates


def test_build_reverse_shape_key_coordinates_uses_basis_coordinates() -> None:
    """Basis を Target にした場合も、その座標を Destination の座標として使う。"""

    basis_coordinates = [(-1.0, 0.0, 1.0), (2.0, 0.5, -0.5)]

    assert build_reverse_shape_key_coordinates(basis_coordinates) == basis_coordinates
