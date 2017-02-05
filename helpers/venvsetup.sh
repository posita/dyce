#!/usr/bin/env bash
# -*- encoding: utf-8; grammar-ext: sh; mode: shell-script -*-

# ========================================================================
# Copyright and other protections apply. Please see the accompanying
# ``LICENSE`` and ``CREDITS`` files for rights and restrictions governing
# use of this software. All rights not expressly waived or licensed are
# reserved. If those files are missing or appear to be modified from their
# originals, then please contact the author before viewing or using this
# software in any capacity.
# ========================================================================

_VENVSETUP_ME="${ME:-${0}}"
_VENVSETUP_BASE_PYTHON="${PYTHON:-python}"
_VENVSETUP_VIRTUALENV="${VIRTUALENV:-virtualenv}"
_VENVSETUP_ZERO_MD5=d41d8cd98f00b204e9800998ecf8427e
_VENVSETUP_DIR="${VENV_DIR:-${PWD}/.venv}"
_VENVSETUP_PYTHON="${_VENVSETUP_DIR}/bin/python"
_VENVSETUP_PIP="${_VENVSETUP_DIR}/bin/pip"

_VENVSETUP_BOOTSTRAP_VERS=15.1.0
_VENVSETUP_BOOTSTRAP_URL="https://pypi.python.org/packages/d4/0c/9840c08189e030873387a73b90ada981885010dd9aea134d6de30cd24cb8/virtualenv-${_VENVSETUP_BOOTSTRAP_VERS}.tar.gz"
_VENVSETUP_BOOTSTRAP_TGZ="/tmp/$( basename "${_VENVSETUP_BOOTSTRAP_URL}" )"
_VENVSETUP_BOOTSTRAP_TGZ_MD5=44e19f4134906fe2d75124427dc9b716
_VENVSETUP_BOOTSTRAP_TGZ_DIR="${_VENVSETUP_BOOTSTRAP_TGZ%.tar.gz}"

_venvsetup() {
    (
        set -e

        if [ ! -e "${_VENVSETUP_PYTHON}" ] \
                || [ ! -e "${_VENVSETUP_PIP}" ] ; then
            if which >/dev/null 2>&1 "${_VENVSETUP_VIRTUALENV}" ; then
                "${_VENVSETUP_VIRTUALENV}" -p "${_VENVSETUP_BASE_PYTHON}" "${_VENVSETUP_DIR}"
            elif "${_VENVSETUP_BASE_PYTHON}" >/dev/null 2>&1 -m virtualenv --version ; then
                "${_VENVSETUP_BASE_PYTHON}" -m virtualenv "${_VENVSETUP_DIR}"
            else
                echo 1>&2 "${_VENVSETUP_ME}: can't find suitable virtualenv; attempting to bootstrap ${_VENVSETUP_BOOTSTRAP_VERS}"
                curl -o "${_VENVSETUP_BOOTSTRAP_TGZ}" "${_VENVSETUP_BOOTSTRAP_URL}"

                if [ "$( md5 </dev/null | sed -E -es'%^.*([0-9A-Fa-f]{32}).*$%\1%' )" = "${_VENVSETUP_ZERO_MD5}" ] ; then
                    tgz_md5="$( md5 "${_VENVSETUP_BOOTSTRAP_TGZ}" | sed -E -es'%^.*([0-9A-Fa-f]{32}).*$%\1%' )"
                elif [ "$( md5sum </dev/null | sed -E -es'%^.*([0-9A-Fa-f]{32}).*$%\1%' )" = "${_VENVSETUP_ZERO_MD5}" ] ; then
                    tgz_md5="$( md5sum "${_VENVSETUP_BOOTSTRAP_TGZ}" | sed -E -es'%^.*([0-9A-Fa-f]{32}).*$%\1%' )"
                else
                    echo 1>&2 "${_VENVSETUP_ME}: can't find MD5 checksum tool; giving up"

                    return 1
                fi

                if [ "${tgz_md5}" != "${_VENVSETUP_BOOTSTRAP_TGZ_MD5}" ] ; then
                    echo 1>&2 "${_VENVSETUP_ME}: MD5 mismatch for ${_VENVSETUP_BOOTSTRAP_TGZ} (expected ${_VENT_TGZ_MD5}; got ${tgz_md5}); giving up"

                    return 1
                fi

                tar -xv -C /tmp -pf "${_VENVSETUP_BOOTSTRAP_TGZ}"
                "${_VENVSETUP_BASE_PYTHON}" "${_VENVSETUP_BOOTSTRAP_TGZ_DIR}/virtualenv.py" "${_VENVSETUP_DIR}"
            fi
        fi

        "${_VENVSETUP_PIP}" install debug flake8 jedi mock pyflakes pylint tox twine typing virtualenv

        if [ -f setup.py ] ; then
            "${_VENVSETUP_PIP}" install --editable .
        fi
    ) \
            || return "${?}"
}

_venvsetup
. "${_VENVSETUP_DIR}/bin/activate"
