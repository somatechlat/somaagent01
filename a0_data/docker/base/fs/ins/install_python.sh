#!/bin/bash
set -e

echo "====================PYTHON START===================="

PYTHON_313_VERSION="${PYTHON_313_VERSION:-3.13.1}"
PYTHON_312_VERSION="${PYTHON_312_VERSION:-3.12.4}"

# ensure latest package index and security updates
apt-get clean
apt-get update
apt-get -y upgrade

# Install toolchain dependencies for building Python releases via pyenv
apt-get install -y --no-install-recommends \
    make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev ca-certificates \
    pkg-config

# Install pyenv globally if not already present
if [ ! -d /opt/pyenv ]; then
    git clone https://github.com/pyenv/pyenv.git /opt/pyenv
fi

# Configure pyenv environment system-wide
cat > /etc/profile.d/pyenv.sh <<'EOF'
if [ "$(id -u)" -eq 0 ]; then
    export PYENV_ROOT="/opt/pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init --path)"
fi
EOF
chmod +x /etc/profile.d/pyenv.sh

export PYENV_ROOT="/opt/pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"

# Build and install required Python versions with pyenv
pyenv install -s "$PYTHON_313_VERSION"
pyenv install -s "$PYTHON_312_VERSION"

echo "====================PYTHON 3.13 VENV===================="
"$PYENV_ROOT/versions/$PYTHON_313_VERSION/bin/python" -m venv /opt/venv
source /opt/venv/bin/activate
pip install --no-cache-dir --upgrade pip ipython requests
deactivate

echo "====================PYENV 3.12 VENV===================="
"$PYENV_ROOT/versions/$PYTHON_312_VERSION/bin/python" -m venv /opt/venv-a0
source /opt/venv-a0/bin/activate
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir \
    torch==2.4.0 \
    torchvision==0.19.0 \
    --index-url https://download.pytorch.org/whl/cpu
deactivate

echo "====================PYTHON UV ===================="
curl -Ls https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh

# Purge caches to keep image lean
"$PYENV_ROOT/versions/$PYTHON_313_VERSION/bin/pip" cache purge || true
"$PYENV_ROOT/versions/$PYTHON_312_VERSION/bin/pip" cache purge || true

# Provide compatibility wrapper scripts for python3.13 commands expected elsewhere
cat <<EOF >/usr/local/bin/python3.13
#!/bin/bash
exec "$PYENV_ROOT/versions/$PYTHON_313_VERSION/bin/python3" "\$@"
EOF
chmod +x /usr/local/bin/python3.13

cat <<EOF >/usr/local/bin/pip3.13
#!/bin/bash
exec "$PYENV_ROOT/versions/$PYTHON_313_VERSION/bin/pip3" "\$@"
EOF
chmod +x /usr/local/bin/pip3.13

echo "====================PYTHON END===================="
