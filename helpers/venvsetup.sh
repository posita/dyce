#!/usr/bin/env bash
# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

_VENVSETUP_BASE_PYTHON="${PYTHON:-python}"
_VENVSETUP_DIR="${VIRTUAL_ENV:-${PWD}/.venv}"

_venvsetup() {
    (
        set -e

        if [ ! -e "${_VENVSETUP_DIR}/bin/python" ] \
                || [ ! -e "${_VENVSETUP_DIR}/bin/pip" ] ; then
            if "${_VENVSETUP_BASE_PYTHON}" >/dev/null 2>&1 -m virtualenv --version ; then
                "${_VENVSETUP_BASE_PYTHON}" -m virtualenv "${_VENVSETUP_DIR}"
            elif "${_VENVSETUP_BASE_PYTHON}" >/dev/null 2>&1 -m venv -h ; then
                "${_VENVSETUP_BASE_PYTHON}" -m venv "${_VENVSETUP_DIR}"
            else
                echo 1>&2 "${0}: can't find suitable virtualenv; giving up"

                return 1
            fi
        fi

        "${_VENVSETUP_DIR}/bin/pip" install --upgrade black debug flake8 jedi mypy pylint pytest tox twine

        if [ -f setup.py ] ; then
            "${_VENVSETUP_DIR}/bin/pip" install --editable .
        fi
    ) \
            || return "${?}"
}

_venvsetup
. "${_VENVSETUP_DIR}/bin/activate"
