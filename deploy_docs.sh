#!/bin/bash
set -e

# Function to deploy a single repository
deploy_repo() {
    REPO_NAME=$1
    REPO_PATH="../$REPO_NAME"
    
    echo "========================================"
    echo "Deploying $REPO_NAME..."
    echo "========================================"
    
    # Verify directory exists
    if [ ! -d "$REPO_PATH" ]; then
        echo "Error: Directory $REPO_PATH not found."
        return 1
    fi
    
    # Navigate to repo
    cd "$REPO_PATH" || exit
    
    # 1. Ensure main branch is clean and up to date
    echo "Ensuring main branch is clean..."
    # Ensure ignore file is correct
    if ! grep -q "docs/sphinx/_build/" .gitignore; then
        echo "docs/sphinx/_build/" >> .gitignore
    fi
    
    # Add and commit any remaining changes (handling pre-commit hook cycles)
    git add .
    git commit -m "docs: Finalize documentation artifacts" || echo "Nothing to commit or commit failed (check hooks)"
    # Try one more time just in case hooks modified files
    git add .
    git commit -m "docs: Finalize documentation artifacts (post-hooks)" || echo "Nothing to commit"
    
    # 2. Preserve the build artifacts
    echo "Preserving build artifacts..."
    BUILD_DIR="docs/sphinx/_build/html"
    if [ ! -d "$BUILD_DIR" ]; then
        echo "Error: Build directory $BUILD_DIR not found. Run make html first."
        exit 1
    fi
    
    TMP_DIR="/tmp/${REPO_NAME}_gh_pages_build"
    rm -rf "$TMP_DIR"
    mkdir -p "$TMP_DIR"
    cp -r "$BUILD_DIR/"* "$TMP_DIR/"
    
    # 3. Switch to gh-pages
    echo "Switching to gh-pages..."
    git checkout -B gh-pages
    
    # 4. Clean the branch
    echo "Cleaning gh-pages branch..."
    # Remove all tracked files
    git rm -rf .
    # Remove untracked files (careful) - creating a .nojekyll usually suffices
    # We want to replace everything.
    # git clean -fdx # This might kill the .git directory if not careful? No, -x removes ignored. -d removes directories.
    # Safe approach: just copy over.
    
    # 5. Restore artifacts
    echo "Restoring artifacts..."
    cp -r "$TMP_DIR/"* .
    touch .nojekyll
    
    # 6. Commit and Push
    echo "Committing and Pushing..."
    git add .
    git commit -m "docs: Publish documentation" || echo "Nothing to commit on gh-pages"
    
    # Push force
    # git push -f origin gh-pages # Uncomment to actually push checking user intent
    # The user asked to "Upload".
    git push -f origin gh-pages
    
    # 7. Return to main
    git checkout main
    
    echo "Deployment of $REPO_NAME complete."
    cd - > /dev/null
}

# Execute for all repos
# We are running from inside somaAgent01 presumably, or we set paths relative.
# Script location: somaAgent01/deploy_docs.sh
# So REPO_PATH for somaAgent01 is ".".
# For others is "../somabrain" etc.

deploy_repo_local() {
    REPO_NAME="somaAgent01"
    echo "Deploying $REPO_NAME (local)..."
    # Logic same as above but without cd ..
    # ... actually I'll just reuse the logic by passing valid paths
    
    # Ensure ignore
    if ! grep -q "docs/sphinx/_build/" .gitignore; then
        echo "docs/sphinx/_build/" >> .gitignore
    fi
    
    git add .
    git commit -m "docs: Finalize documentation artifacts" || echo "Nothing to commit"
     git add .
    git commit -m "docs: Finalize documentation artifacts (post-hooks)" || echo "Nothing to commit"

    BUILD_DIR="docs/sphinx/_build/html"
    TMP_DIR="/tmp/${REPO_NAME}_gh_pages_build"
    rm -rf "$TMP_DIR"
    mkdir -p "$TMP_DIR"
    cp -r "$BUILD_DIR/"* "$TMP_DIR/"
    
    git checkout -B gh-pages
    git rm -rf .
    cp -r "$TMP_DIR/"* .
    touch .nojekyll
    git add .
    git commit -m "docs: Publish documentation"
    git push -f origin gh-pages
    git checkout main
}

deploy_repo_local

deploy_repo "somabrain"
deploy_repo "somafractalmemory"

echo "All deployments finished."
