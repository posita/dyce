
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

PKG="$( python -c 'import configparser, sys ; config = configparser.ConfigParser() ; config.read_file(open(sys.argv[1])) ; print(config.get("metadata", "name"))' "${_REPO_DIR}/setup.cfg" )"
MAJOR="${1}"
MINOR="${2}"
PATCH="${3}"
VERS="${MAJOR}.${MINOR}"
VERS_PATCH="${VERS}.${PATCH}"
TAG="v${VERS_PATCH}"

set -ex
cd "${_REPO_DIR}"
twine --version
mkdocs --version
mike --version
git checkout -b "${VERS_PATCH}-release"
perl -pi -e "s{^__version__\\b([^#=]*)=\\s*\\(\\s*0\\s*,\\s*0\\s*,\\s*0\\s*,?\\s*\\)(\\s*#.*)?\$} {__version__\\1= (${MAJOR}, ${MINOR}, ${PATCH})\\2}g" dyce/version.py
perl -pi -e "s{^version\\s+=\\s+0.0.0\$} {version = ${MAJOR}.${MINOR}.${PATCH}}g" setup.cfg
perl -pi -e "s{\\.github\\.io/dyce/latest/([^)]*)\\)} {\\.github\\.io/dyce/${VERS}/\\1)}g ; s{/dyce/([^/]+/)*latest/} {/dyce/\\1${TAG}/}g ; s{//pypi\\.org/([^/]+/)?${PKG}/} {//pypi.org/\\1${PKG}/${VERS_PATCH}/}g ; s{/pypi/([^/]+/)?${PKG}\\.svg\\)} {/pypi/\\1${PKG}/${VERS_PATCH}.svg)}g" setup.cfg README.md docs/contrib.md

problem_areas="$(
    grep -En '/latest\b' /dev/null README.md docs/*.md || [ "${?}" -eq 1 ]
    grep -En "^#+\\s+${MAJOR}\\.${MINOR}\\.${PATCH}([^[:alnum:]]|$)" /dev/null docs/notes.md || [ "${?}" -eq 1 ]
)"

set +x

if [ -n "${problem_areas}" ] ; then
    echo '- - - - POTENTIAL PROBLEM AREAS - - - -'
    echo "${problem_areas}"
    echo '- - - - - - - - - - - - - - - - - - - -'

    sh=$(ps -o comm -p "${$}" | awk 'NR == 2')
    printf "Potential problem areas detected. Continue anyway [Y/n]? "

    while true ; do
        if [ "${sh%/zsh}" != "${sh}" ] ; then
            read -k 1 -s  # zsh
        else
            read -n 1 -s  # everywhere else
        fi

        case "${REPLY}" in
            Y|y|$'\n'|'')
                REPLY=y
                echo 'yes'
                break
                ;;
            N|n)
                REPLY=n
                echo 'no'
                break
                ;;
        esac

        printf '\n[Y/n]? '
    done
fi

if [ "${REPLY}" == n ] ; then
    git status

    exit 1
fi

set -ex
git commit --all --message "Update version and release ${TAG}."
tox
python -c 'from setuptools import setup ; setup()' bdist_wheel sdist
twine check "dist/${PKG}-${VERS_PATCH}"[-.]*
mike deploy --rebase --update-aliases "${VERS}" latest
git tag --force --message "$( cat <<EOF
Release ${TAG}.

<TODO: Copy ${VERS_PATCH} [release notes](docs/notes.md) here. Hope you were keeping track!>
EOF
)" "${TAG}"
