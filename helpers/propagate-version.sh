#!/usr/bin/env bash
set -eu -o pipefail

_MY_DIR="$( cd "$( dirname "${0}" )" && pwd )"
_REPO_DIR="$( git -C "${_MY_DIR}" rev-parse --show-toplevel )"

case "${#}" in
    0)
        true
        ;;
    1)
        VERS_PATCH="${1}"
        ;;
    2)
        echo 1>&2 "usage: ${0} [VERS_PATCH]"

        exit 1
        ;;
esac

. "${_MY_DIR}/ci-vars.sh"  # also defines _VERS_REGEX

perl -p -i -e "
  s{\\.github\\.io/${PROJECT}/\\d+\\.\\d+\\/([^) \"]*)} {\\.github\\.io/${PROJECT}/${VERS}/\\1}g ;
  s{/${PROJECT}/([^/]+/)*v${_VERS_REGEX}([/?])} {/${PROJECT}/\\1${TAG}\\3}g ;
  s{//pypi\\.org/([^/]+/)?${PKG}/${_VERS_REGEX}/} {//pypi.org/\\1${PKG}/${VERS_PATCH}/}g ;
  s{/pypi/([^/]+/)?${PKG}/${_VERS_REGEX}\\.svg\\)} {/pypi/\\1${PKG}/${VERS_PATCH}.svg)}g ;
" "${_REPO_DIR}/README.md"

perl -p -i -e "
  s{__vers_str__\\b\\s*:\\s*${_VERS_REGEX}\\b} {__vers_str__: ${VERS_PATCH}}g ;
" "${_REPO_DIR}/mkdocs.yml"
