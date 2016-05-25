#!/usr/bin/env sh
#-*- encoding: utf-8; mode: sh; grammar-ext: sh -*-

#=========================================================================
# Copyright (c) 2015 Matt Bogosian <mtb19@columbia.edu>.
#
# Please see the accompanying LICENSE (or LICENSE.txt) file for rights and
# restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If such a file did not accompany this
# software, then please contact the author before viewing or using this
# software in any capacity.
#=========================================================================

_MY_DIR="$( cd "$( dirname "${0}" )" && pwd )"
set -ex
[ -d "${_MY_DIR}" ]
[ "${_MY_DIR}/runtests.sh" -ef "${0}" ]
cd "${_MY_DIR}"
exec tox ${TOX_ENV:+-e} ${TOX_ENV}
