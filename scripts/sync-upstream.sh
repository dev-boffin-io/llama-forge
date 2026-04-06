#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# llama-forge — Upstream Sync Script
# Maintainer: Boffin <tradeguruboffin@gmail.com>
# Usage: bash ~/llama-forge-sync.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# ── Config ────────────────────────────────────────────────────
REPO="/opt/llama-forge"
REMOTE="git@github.com:dev-boffin-io/llama-forge.git"
UPSTREAM="upstream/master"
BACKUP="/tmp/llama_forge_sync_bak"
SELF="$(realpath "$0")"  # path of this script itself

# Custom files to preserve across upstream resets
CUSTOM_FILES=(
    "README.md"
    "AGENTS.md"
    "CONTRIBUTING.md"
    "SECURITY.md"
    "AUTHORS"
    "LICENSE"
    ".gitattributes"
    "CMakeLists.txt"
    "scripts/sync-upstream.sh"
)

# ── Colors ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { echo -e "${CYAN}==>${RESET} ${BOLD}$*${RESET}"; }
success() { echo -e "${GREEN}  ✔${RESET} $*"; }
warn()    { echo -e "${YELLOW}  ⚠${RESET} $*"; }
error()   { echo -e "${RED}  ✘ ERROR:${RESET} $*" >&2; }
die()     { error "$*"; exit 1; }

# ── Sanity Checks ─────────────────────────────────────────────
info "Checking environment..."

[ -d "$REPO" ]       || die "Repo not found: $REPO"
[ -d "$REPO/.git" ]  || die "Not a git repository: $REPO"

cd "$REPO"

git remote get-url upstream &>/dev/null \
    || die "Remote 'upstream' not configured. Run:\n  git remote add upstream https://github.com/ggml-org/llama.cpp.git"

git remote get-url origin &>/dev/null \
    || die "Remote 'origin' not configured."

success "Environment OK"

# ── Abort any in-progress merge/rebase ────────────────────────
info "Cleaning up any in-progress operations..."
git merge --abort  2>/dev/null && warn "Aborted in-progress merge"  || true
git rebase --abort 2>/dev/null && warn "Aborted in-progress rebase" || true
git cherry-pick --abort 2>/dev/null || true

# ── Backup ────────────────────────────────────────────────────
info "Creating backup..."
rm -rf "$BACKUP"
mkdir -p "$BACKUP/custom_files/scripts"

# Backup llama_gui
if [ -d "$REPO/llama_gui" ]; then
    cp -r "$REPO/llama_gui" "$BACKUP/llama_gui"
    success "Backed up: llama_gui/"
else
    warn "llama_gui/ not found — skipping GUI backup"
fi

# Backup this script itself from $HOME
if [ -f "$SELF" ]; then
    cp "$SELF" "$BACKUP/sync-script-self.sh"
    success "Backed up: sync script itself ($SELF)"
fi

# Backup custom files
for f in "${CUSTOM_FILES[@]}"; do
    if [ -f "$REPO/$f" ]; then
        dir=$(dirname "$BACKUP/custom_files/$f")
        mkdir -p "$dir"
        cp "$REPO/$f" "$BACKUP/custom_files/$f"
        success "Backed up: $f"
    else
        warn "Not found, skipping: $f"
    fi
done

# ── Fetch Upstream ────────────────────────────────────────────
info "Fetching upstream..."
git fetch upstream || die "Failed to fetch upstream"

UPSTREAM_SHA=$(git rev-parse "$UPSTREAM")
LOCAL_SHA=$(git rev-parse HEAD)

if [ "$UPSTREAM_SHA" = "$LOCAL_SHA" ]; then
    warn "Already up to date with upstream."
    NEEDS_PUSH=false
else
    success "New upstream commits found"
    NEEDS_PUSH=true
fi

# ── Reset to Upstream ─────────────────────────────────────────
info "Resetting to $UPSTREAM..."
git reset --hard "$UPSTREAM" || die "git reset failed"
success "Reset to $(git rev-parse --short HEAD)"

# ── Restore Custom Files ──────────────────────────────────────
info "Restoring custom files..."

if [ -d "$BACKUP/llama_gui" ]; then
    rm -rf "$REPO/llama_gui"
    cp -r "$BACKUP/llama_gui" "$REPO/llama_gui"
    success "Restored: llama_gui/"
fi

for f in "${CUSTOM_FILES[@]}"; do
    if [ -f "$BACKUP/custom_files/$f" ]; then
        dir=$(dirname "$REPO/$f")
        mkdir -p "$dir"
        cp "$BACKUP/custom_files/$f" "$REPO/$f"
        success "Restored: $f"
    fi
done

# Restore script to $HOME as well
if [ -f "$BACKUP/sync-script-self.sh" ]; then
    cp "$BACKUP/sync-script-self.sh" "$SELF"
    chmod +x "$SELF"
    success "Restored: sync script to $SELF"
fi

# Cleanup backup
rm -rf "$BACKUP"

# ── Stage & Commit ────────────────────────────────────────────
info "Staging changes..."

git add llama_gui/ 2>/dev/null || true
for f in "${CUSTOM_FILES[@]}"; do
    git add "$f" 2>/dev/null || true
done

if git diff --cached --quiet; then
    success "Nothing to commit — already up to date."
    NEEDS_PUSH=false
else
    COMMIT_MSG="chore: sync upstream $(git rev-parse --short upstream/master)"
    git commit -m "$COMMIT_MSG"
    success "Committed: $COMMIT_MSG"
    NEEDS_PUSH=true
fi

# ── Push ──────────────────────────────────────────────────────
if [ "$NEEDS_PUSH" = true ]; then
    info "Pushing to origin..."
    git push --force "$REMOTE" master \
        && success "Pushed to $REMOTE" \
        || die "Push failed. Check SSH key: ssh -T git@github.com"
else
    info "No push needed."
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}─────────────────────────────────────────${RESET}"
echo -e "${GREEN}${BOLD}  ✔  Sync complete!${RESET}"
echo -e "${GREEN}${BOLD}─────────────────────────────────────────${RESET}"
echo ""
echo -e "  Upstream : $(git rev-parse --short upstream/master)"
echo -e "  Local    : $(git rev-parse --short HEAD)"
echo ""
echo -e "  To rebuild: ${CYAN}cmake --build $REPO/build${RESET}"
echo ""
