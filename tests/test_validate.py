"""Unit tests for the runtime properties validator."""

from __future__ import annotations

import pytest

from tgram_analytics._validate import validate_properties


class TestAcceptsScalars:
    def test_string(self) -> None:
        validate_properties({"s": "x"}, "track")

    def test_int_float_bool_none(self) -> None:
        validate_properties({"i": 1, "f": 1.5, "b": True, "z": None}, "track")

    def test_empty_dict(self) -> None:
        validate_properties({}, "track")


class TestAcceptsScalarArrays:
    def test_string_list(self) -> None:
        validate_properties({"tags": ["a", "b", "c"]}, "track")

    def test_int_list(self) -> None:
        validate_properties({"scores": [1, 2, 3]}, "track")

    def test_bool_list(self) -> None:
        validate_properties({"flags": [True, False]}, "track")

    def test_heterogeneous_scalar_list(self) -> None:
        validate_properties({"mixed": ["a", 1, True, None]}, "track")

    def test_empty_list(self) -> None:
        validate_properties({"empty": []}, "track")


class TestRejectsBadShapes:
    def test_top_level_dict_value(self) -> None:
        with pytest.raises(TypeError, match="nested"):
            validate_properties({"nested": {"a": 1}}, "track")

    def test_top_level_tuple_value(self) -> None:
        # tuples are sequence-like; reject them so callers don't get
        # surprised by a list reshape on the wire.
        with pytest.raises(TypeError, match="bad"):
            validate_properties({"bad": (1, 2)}, "track")

    def test_top_level_set_value(self) -> None:
        with pytest.raises(TypeError, match="bad"):
            validate_properties({"bad": {1, 2}}, "track")

    def test_dict_inside_list(self) -> None:
        with pytest.raises(TypeError) as exc:
            validate_properties({"tags": [{"x": 1}]}, "track")
        assert "tags" in str(exc.value)

    def test_nested_list(self) -> None:
        with pytest.raises(TypeError) as exc:
            validate_properties({"tags": [[1, 2]]}, "track")
        assert "tags" in str(exc.value)

    def test_list_with_none_is_ok_but_other_objects_not(self) -> None:
        # None is a scalar.
        validate_properties({"vals": [None, "a"]}, "track")
        with pytest.raises(TypeError):
            validate_properties({"vals": [None, object()]}, "track")

    def test_error_message_mentions_method(self) -> None:
        with pytest.raises(TypeError, match="identify"):
            validate_properties({"x": object()}, "identify")

    def test_error_message_mentions_bad_index(self) -> None:
        with pytest.raises(TypeError) as exc:
            validate_properties({"tags": ["a", {}]}, "track")
        # Index 1 should be mentioned.
        assert "1" in str(exc.value)
