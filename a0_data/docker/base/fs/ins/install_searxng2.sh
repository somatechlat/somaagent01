#!/bin/bash
set -e

echo "====================SEARXNG2 START===================="


# clone SearXNG repo
git clone "https://github.com/searxng/searxng" \
                   "/usr/local/searxng/searxng-src"

echo "====================SEARXNG2 VENV===================="

PYTHON_BIN="${PYTHON_BIN:-/usr/local/bin/python3.13}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python interpreter '$PYTHON_BIN' not found" >&2
    exit 1
fi
PYTHON_BIN="$(command -v "$PYTHON_BIN")"

# create virtualenv without relying on ensurepip
"$PYTHON_BIN" -m venv --without-pip "/usr/local/searxng/searx-pyenv"

# make it default
echo ". /usr/local/searxng/searx-pyenv/bin/activate" \
                   >>  "/usr/local/searxng/.profile"

# activate venv
source "/usr/local/searxng/searx-pyenv/bin/activate"

# bootstrap pip explicitly
curl -sS https://bootstrap.pypa.io/get-pip.py | python

echo "====================SEARXNG2 INST===================="

# update pip's boilerplate
pip install --no-cache-dir -U pip setuptools wheel pyyaml lxml

# jump to SearXNG's working tree and install SearXNG into virtualenv
cd "/usr/local/searxng/searxng-src"
pip install --no-cache-dir --use-pep517 --no-build-isolation -e .

# cleanup cache
pip cache purge

echo "====================SEARXNG2 END===================="