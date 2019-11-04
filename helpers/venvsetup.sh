#!/usr/bin/env bash
# -*- encoding: utf-8 -*-
# ======================================================================
# Copyright and other protections apply. Please see the accompanying
# LICENSE and CREDITS files for rights and restrictions governing use of
# this software. All rights not expressly waived or licensed are
# reserved. If those files are missing or appear to be modified from
# their originals, then please contact the author before viewing or
# using this software in any capacity.
# ======================================================================

_VENVSETUP_ME="${ME:-${0}}"
_VENVSETUP_BASE_PYTHON="${PYTHON:-python}"
_VENVSETUP_DIR="${VIRTUAL_ENV:-${PWD}/.venv}"
_VENVSETUP_PYTHON="${_VENVSETUP_DIR}/bin/python"
_VENVSETUP_PIP="${_VENVSETUP_DIR}/bin/pip"

_VENVSETUP_BOOTSTRAP_URL="https://files.pythonhosted.org/packages/e7/80/15d28e5a075fb02366ce97558120bb987868dab3600233ec7be032dc6d01/virtualenv-16.7.7.tar.gz"
_VENVSETUP_BOOTSTRAP_VERS="${_VENVSETUP_BOOTSTRAP_URL%.tar.gz}"
_VENVSETUP_BOOTSTRAP_VERS="${_VENVSETUP_BOOTSTRAP_VERS##*-}"
_VENVSETUP_BOOTSTRAP_TGZ="/tmp/$( basename "${_VENVSETUP_BOOTSTRAP_URL}" )"
_VENVSETUP_BOOTSTRAP_TGZ_SHA256=d257bb3773e48cac60e475a19b608996c73f4d333b3ba2e4e57d5ac6134e0136
_VENVSETUP_BOOTSTRAP_TGZ_DIR="${_VENVSETUP_BOOTSTRAP_TGZ%.tar.gz}"

_venvsetup() {
    (
        set -e

        if [ ! -e "${_VENVSETUP_PYTHON}" ] \
                || [ ! -e "${_VENVSETUP_PIP}" ] ; then
            if "${_VENVSETUP_BASE_PYTHON}" >/dev/null 2>&1 -m virtualenv --version ; then
                "${_VENVSETUP_BASE_PYTHON}" -m virtualenv "${_VENVSETUP_DIR}"
            else
                echo 1>&2 "${_VENVSETUP_ME}: can't find suitable virtualenv; attempting to bootstrap ${_VENVSETUP_BOOTSTRAP_VERS}"
                curl -o "${_VENVSETUP_BOOTSTRAP_TGZ}" "${_VENVSETUP_BOOTSTRAP_URL}"

                if ! which >/dev/null 2>&1 openssl ; then
                    echo 1>&2 "${_VENVSETUP_ME}: can't find openssl; giving up"

                    return 1
                fi

                tgz_sha256="$( openssl dgst -r -sha256 "${_VENVSETUP_BOOTSTRAP_TGZ}" | cut -c 1-64 )"

                if [ "${tgz_sha256}" != "${_VENVSETUP_BOOTSTRAP_TGZ_SHA256}" ] ; then
                    echo 1>&2 "${_VENVSETUP_ME}: SHA-256 mismatch for ${_VENVSETUP_BOOTSTRAP_TGZ} (expected ${_VENVSETUP_BOOTSTRAP_TGZ_SHA256}; got ${tgz_sha256}); giving up"

                    return 1
                fi

                tar -xv -C /tmp -pf "${_VENVSETUP_BOOTSTRAP_TGZ}"
                "${_VENVSETUP_BASE_PYTHON}" "${_VENVSETUP_BOOTSTRAP_TGZ_DIR}/virtualenv.py" "${_VENVSETUP_DIR}"
            fi
        fi

        "${_VENVSETUP_PIP}" install --upgrade debug flake8 jedi pylint pytest tox twine virtualenv
        [ ! -f tests/requirements.txt ] \
            || "${_VENVSETUP_PIP}" install -rtests/requirements.txt
        "${_VENVSETUP_PIP}" install --upgrade mypy \
            || true

        if [ -f setup.py ] ; then
            "${_VENVSETUP_PIP}" install --editable .
        fi
    ) \
            || return "${?}"
}

_venvsetup
. "${_VENVSETUP_DIR}/bin/activate"
