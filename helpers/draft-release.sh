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
[ "${_MY_DIR}/draft-release.sh" -ef "${0}" ]
cd "${_REPO_DIR}"

if [ "${#}" -ne 3 ] ; then
    echo 1>&2 "usage: $( basename "${0}" ) MAJOR MINOR PATCH"

    exit 1
fi

PKG="$( python -c 'import setup ; print(setup.SETUP_ARGS["name"])' )"
VERS_PY="$( python -c 'import setup ; print(setup.vers_info["__path__"])' )"
MAJOR="${1}"
MINOR="${2}"
PATCH="${3}"
VERS="${MAJOR}.${MINOR}"
VERS_PATCH="${VERS}.${PATCH}"
TAG="v${VERS_PATCH}"

set -ex
( cd "${_REPO_DIR}" ; tox )
git checkout -b "${VERS_PATCH}-release"
perl -pi -e 's{^__version__([^#=]*)=\s*\(\s*0\s*,\s*0\s*,\s*0\s*,?\s*\)(\s*#.*)?$}{__version__\1= ('"${MAJOR}"', '"${MINOR}"', '"${PATCH}"')\2}g ;' "${VERS_PY}"
perl -pi -e 's{\.github\.io/dyce/latest/\)}{\.github\.io/dyce/'"${VERS}"'/)}g ; s{/master/}{/'"${TAG}"'/}g ; s{\?version=master\)}{?version='"${TAG}"')}g ; s{!\[master ([^\]]+)\]}{!['"${TAG}"' \1]}g ; s{/pypi/([^/]+/)?'"${PKG}"'(\.svg)?\)} {/pypi/\1'"${PKG}"'/'"${VERS_PATCH}"'\2)}g' README.md
perl -pi -e 's{!\[master ([^\]]+)\]}{!['"${TAG}"' \1]}g ; s{/pypi/([^/]+/)?'"${PKG}"'(\.svg)?\)} {/pypi/\1'"${PKG}"'/'"${VERS_PATCH}"'\2)}g' docs/index.md
git commit --all --message "Update version and release ${TAG}."
git tag --sign --force --message "Release ${TAG}." "${TAG}"
python setup.py bdist_wheel sdist
twine check "dist/${PKG}-${VERS_PATCH}"[-.]*
mike deploy --rebase --update-aliases "${VERS}" latest
