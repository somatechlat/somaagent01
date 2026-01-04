#!/bin/bash
set -e

# Function to deploy a single repository
deploy_repo() {
    REPO_NAME=$1
    REPO_DIR=$2
    
    echo "========================================"
    echo "Processing $REPO_NAME"
    echo "========================================"
    
    # Use subshell to isolate directory changes and environment
    (
        cd "$REPO_DIR" || exit 1
        
        # Activate venv if it exists and is valid
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        elif [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi
        
        # Install sphinx if needed
        if ! python3 -m pip show sphinx &> /dev/null; then
            echo "Installing Sphinx dependencies..."
            python3 -m pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
        fi
        
        echo "Building documentation..."
        cd docs/sphinx || exit 1
        make clean
        # Use python3 -m sphinx to ensure we use the venv python
        make html SPHINXBUILD="python3 -m sphinx"
        cd ../..
        
        echo "Deploying to gh-pages..."
        
        # 1. Ensure main branch is clean
        if ! grep -q "docs/sphinx/_build/" .gitignore; then
            echo "docs/sphinx/_build/" >> .gitignore
        fi
        
        git add .
        git commit -m "docs: Finalize artifacts" || echo "Nothing to commit"
        
        # 2. Preserve artifacts
        BUILD_DIR="docs/sphinx/_build/html"
        TMP_DIR="/tmp/${REPO_NAME}_gh_pages_build"
        rm -rf "$TMP_DIR"
        mkdir -p "$TMP_DIR"
        cp -r "$BUILD_DIR/"* "$TMP_DIR/"
        
        # 3. Switch to gh-pages
        git checkout -B gh-pages
        
        # 4. Clean and restore
        git rm -rf .
        cp -r "$TMP_DIR/"* .
        touch .nojekyll
        
        # 5. Push
        git add .
        git commit -m "docs: Publish documentation" || echo "Nothing to commit"
        git push -f origin gh-pages
        
        # 6. Return
        git checkout main
        # Sync main with django if desired, but let's stick to docs deployment.
    )
}

# Deploy SomaAgent01 (Current Dir)
deploy_repo "somaAgent01" "."

# Deploy SomaBrain
deploy_repo "somabrain" "../somabrain"

# Deploy SomaFractalMemory
deploy_repo "somafractalmemory" "../somafractalmemory"

echo "All deployments completed successfully."
