#!/usr/bin/env sh
# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

_MY_DIR="$( cd "$( dirname "${0}" )" && pwd )"
_REPO_DIR="$( cd "${_MY_DIR}${_MY_DIR:+/}.." && pwd )"
set -ex
[ -d "${_REPO_DIR}" ]
[ "${_MY_DIR}/runtests.sh" -ef "${0}" ]
cd "${_REPO_DIR}"
exec tox "${@}"
