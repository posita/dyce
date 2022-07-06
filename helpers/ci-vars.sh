_VERS_REGEX='(\d+\.\d+)\.\d+(?:\.post\d+\+g[0-9a-f]{7}(?:\.d\d{8})?|\+d\d{8})?'
_VERS_PATCH="$( python -m versioningit )"
VERS_PATCH="${VERS_PATCH-${_VERS_PATCH}}"
VERS="$( echo "${VERS_PATCH}" | perl -pe "s/^${_VERS_REGEX}\$/\1/" )"
TAG="v${VERS_PATCH}"

PROJECT="$( python -c "
import configparser, pathlib, sys, urllib.parse
config = configparser.ConfigParser()
config.read_file(open(sys.argv[1]))
url = urllib.parse.urlparse(config.get(\"metadata\", \"url\"))
project = pathlib.PurePath(url.path).parts[1]
print(project)
" setup.cfg )"

PKG="$( python -c "
import configparser, sys
config = configparser.ConfigParser()
config.read_file(open(sys.argv[1]))
name = config.get(\"metadata\", \"name\")
print(name)
" setup.cfg )"

printf 'PKG=%q\n' "${PKG}"
printf 'PROJECT=%q\n' "${PROJECT}"
printf 'TAG=%q\n' "${TAG}"
printf 'VERS=%q\n' "${VERS}"
printf 'VERS_PATCH=%q\n' "${VERS_PATCH}"
