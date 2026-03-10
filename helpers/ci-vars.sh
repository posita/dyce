_VERS_REGEX='(\d+\.\d+)\.\d+(?:\.post\d+\+g[0-9a-f]{7}(?:\.d\d{8})?|\+d\d{8})?'
_VERS_PATCH="$( python3 -m versioningit )"
VERS_PATCH="${VERS_PATCH-${_VERS_PATCH}}"
VERS="$( echo "${VERS_PATCH}" | perl -pe "s/^${_VERS_REGEX}\$/\1/" )"
TAG="v${VERS_PATCH}"

PROJECT="$( python3 -c "
import pathlib, sys, urllib.parse
try:
    import tomllib
except ImportError:
    # TODO(posita): Remove when retiring support for 3.10
    import tomli as tomllib
with open(sys.argv[1], \"rb\") as f:
    config = tomllib.load(f)
url = urllib.parse.urlparse(config[\"project\"][\"urls\"][\"Homepage\"])
project = pathlib.PurePath(url.path).parts[1]
print(project)
" pyproject.toml )"

PKG="$( python3 -c "
import sys
try:
    import tomllib
except ImportError:
    # TODO(posita): Remove when retiring support for 3.10
    import tomli as tomllib
with open(sys.argv[1], \"rb\") as f:
    config = tomllib.load(f)
print(config[\"project\"][\"name\"])
" pyproject.toml )"

printf 'PKG=%q\n' "${PKG}"
printf 'PROJECT=%q\n' "${PROJECT}"
printf 'TAG=%q\n' "${TAG}"
printf 'VERS=%q\n' "${VERS}"
printf 'VERS_PATCH=%q\n' "${VERS_PATCH}"
