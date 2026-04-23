# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please keep each docstring sentence on its own unwrapped line. It looks like crap in a
# text editor, but it has no effect on rendering, and it allows much more useful diffs.
# (This does not apply to code comments.) Thank you!
# ======================================================================================

import warnings

import pytest

from dyce.lifecycle import experimental

__all__ = ()


class TestExperimental:
    def test_emits_user_warning(self) -> None:
        @experimental
        def _fn() -> int:
            return 1

        with pytest.warns(UserWarning, match=r"experimental"):
            _fn()

    def test_return_value_preserved(self) -> None:
        @experimental
        def _fn() -> str:
            return "hello"

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            assert _fn() == "hello"

    def test_docstring_has_admonition(self) -> None:
        @experimental
        def _fn() -> None:
            r"""Original docstring."""

        assert _fn.__doc__ is not None
        assert '!!! warning "Experimental"' in _fn.__doc__
        assert "Original docstring." in _fn.__doc__

    def test_docstring_no_original(self) -> None:
        @experimental
        def _fn() -> None:
            pass

        assert _fn.__doc__ is not None
        assert '!!! warning "Experimental"' in _fn.__doc__

    def test_functools_wraps_preserves_name(self) -> None:
        @experimental
        def my_function() -> None:
            pass

        assert my_function.__name__ == "my_function"

    def test_warning_message_contains_qualname(self) -> None:
        @experimental
        def _fn() -> None:
            pass

        with pytest.warns(UserWarning, match=r"fn"):
            _fn()
