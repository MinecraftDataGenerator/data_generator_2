#!/usr/bin/env bash
set -euo pipefail

START_VERSION="18w01a"
WORK_DIR="/tmp/datagenerator"
TOOLS_DIR="/tmp/mc_tools"
SKIP_FILE="skip_version.txt"

# 1. Ensure we are in the repository root directory
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# 1. Ensure we are in the repository root directory
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Load versions to skip from skip_version.txt immediately
if [[ -f "$SKIP_FILE" ]]; then
    echo "==> Loading skip list from $SKIP_FILE..."
    while IFS= read -r version; do
        version=$(echo "$version" | xargs)
        [[ -n "$version" ]] && echo "    - Skipping: $version"
    done < "$SKIP_FILE"
fi

MAIN_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# 2. Backup helper scripts to a temporary directory
# This keeps them accessible even when switching/clearing orphan branches
echo "==> Backing up helper scripts to $TOOLS_DIR..."
rm -rf "$TOOLS_DIR"
mkdir -p "$TOOLS_DIR"
cp manifest.py download.py run_generator.sh "$TOOLS_DIR/"
chmod +x "$TOOLS_DIR/run_generator.sh"

# Sanitize version name to valid git branch name
sanitize_branch_name() {
    local name="$1"
    # Replace spaces with hyphens, remove invalid characters, lowercase
    name=$(echo "$name" | tr ' ' '-' | sed 's/[^a-zA-Z0-9._-]//g' | tr '[:upper:]' '[:lower:]')
    echo "$name"
}

# 3. Execute manifest.py and fetch the version list
echo "==> Fetching version list via manifest.py..."
MANIFEST_OUTPUT=$(python3 "$TOOLS_DIR/manifest.py")
VERSIONS_LINE=$(echo "$MANIFEST_OUTPUT" | grep "^versions=" | cut -d= -f2)

IFS=',' read -ra ALL_VERSIONS <<< "$VERSIONS_LINE"

# 4. Fetch all remote branches for accurate existence checks
echo "==> Updating remote branch information..."
git fetch origin --prune

start_processing=false
previous_branch=""

for version in "${ALL_VERSIONS[@]}"; do
    version=$(echo "$version" | xargs)
    branch_name=$(sanitize_branch_name "$version")

    if [[ "$version" == "$START_VERSION" ]]; then
        start_processing=true
    fi

    if [[ "$start_processing" == "false" ]]; then
        continue
    fi

    # Check if version is in skip list
    if grep -q "^${version}$" "$SKIP_FILE" 2>/dev/null; then
        echo "--> Version '$version' is broken (in skip list). Skipping..."
        continue
    fi

    # Check if branch already exists locally or remotely
    if git rev-parse --verify --quiet "refs/heads/$branch_name" >/dev/null || \
       git rev-parse --verify --quiet "refs/remotes/origin/$branch_name" >/dev/null; then
        echo "--> Branch '$branch_name' (version: $version) already exists. Skipping..."
        previous_branch="$branch_name"
        continue
    fi

    echo "=================================================="
    echo "Processing new version: $version (branch: $branch_name)"
    echo "=================================================="

    # Clean temporary working directory
    rm -rf "$WORK_DIR"
    mkdir -p "$WORK_DIR"

    # Download server JAR
    echo "--> Downloading server JAR..."
    python3 "$TOOLS_DIR/download.py" "$version" "$WORK_DIR"

    # Run Data Generator
    echo "--> Running Data Generator..."
    (
        cd "$WORK_DIR"
        "$TOOLS_DIR/run_generator.sh" "$WORK_DIR/server.jar"
    )

    # Create/checkout target branch
    if [[ -z "$previous_branch" ]]; then
        echo "--> First target ($START_VERSION): Creating orphan branch..."
        git checkout --orphan "$branch_name"
        git rm -rf . >/dev/null 2>&1 || true
        git clean -fdx
    else
        echo "--> Creating branch '$branch_name' based on '$previous_branch'..."
        git checkout -b "$branch_name" "$previous_branch"
    fi

    # Copy generated data into repository root
    echo "--> Copying generated data into repository..."
    cp -r "$WORK_DIR"/* ./ 2>/dev/null || true

    # Create .gitignore to exclude unwanted folders and files
    cat << 'EOF' > .gitignore
assets/
libraries/
versions/
.idea/
server.jar
EOF

    # Clean any ignored untracked files brought over during copying
    git clean -fdX

    # Always create/overwrite README.md to reflect the current version
    echo "# Minecraft Data - $version" > README.md

    # Commit and Push
    git add -A

    # Commit with --allow-empty as a safety fallback
    echo "--> Committing and pushing branch '$branch_name'..."
    git commit --allow-empty -m "Add generated data for Minecraft $version"
    git push origin "$branch_name"

    previous_branch="$branch_name"

    # Switch back to main branch for next iteration
    git checkout "$MAIN_BRANCH"
done

# Cleanup temporary tools and data directories
rm -rf "$WORK_DIR" "$TOOLS_DIR"
echo "==> Done! All new versions have been processed."