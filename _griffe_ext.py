# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

r"""
Griffe extension that injects an Experimental admonition into docstrings at parse
time.

Detects `@experimental` from `dyce.lifecycle` and prepends the corresponding MkDocs
admonition to the object’s docstring, mirroring what the runtime decorator does to
`__doc__`.

`@deprecated` admonitions are handled by `griffe-warnings-deprecated`.
"""

import griffe

from dyce.lifecycle import experimental_msg

__all__ = ("LifecycleExtension",)

_EXPERIMENTAL_TARGET = "dyce.lifecycle.experimental"


def _resolve(obj: griffe.Object, name: str) -> str:
    r"""Resolve *name* to its fully-qualified target path via the enclosing module’s aliases."""
    node: griffe.Object | griffe.Alias | None = obj.parent
    while node is not None and not isinstance(node, griffe.Module):
        node = node.parent
    if node is not None and name in node.members:
        member = node.members[name]
        if isinstance(member, griffe.Alias):
            return member.target_path
    return name


class LifecycleExtension(griffe.Extension):
    r"""Prepend an Experimental admonition to docstrings of decorated callables."""

    def on_function_instance(
        self,
        *,
        func: griffe.Function,
        **_kwargs: object,
    ) -> None:
        r"""Process functions and methods."""
        self._annotate(func)

    def on_class_instance(
        self,
        *,
        cls: griffe.Class,
        **_kwargs: object,
    ) -> None:
        r"""Process classes."""
        self._annotate(cls)

    def _annotate(self, obj: griffe.Class | griffe.Function) -> None:
        for decorator in obj.decorators:
            if _resolve(obj, str(decorator.value)) == _EXPERIMENTAL_TARGET:
                msg = experimental_msg % obj.path
                self._prepend(obj, "Experimental", msg)
                break

    def _prepend(
        self,
        obj: griffe.Class | griffe.Function,
        title: str,
        msg: str,
    ) -> None:
        admonition = f'!!! warning "{title}"\n\n    {msg}'
        if obj.docstring is None:
            obj.docstring = griffe.Docstring(admonition, parent=obj)
        else:
            obj.docstring.value = admonition + "\n\n" + obj.docstring.value
