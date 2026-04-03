#!/bin/bash
# Sentient Arena Cohort 0 — Day 1 Setup Script
# Run: chmod +x scripts/setup.sh && ./scripts/setup.sh
set -e

echo "=== Arena Competition Setup ==="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+ first."
    exit 1
fi
PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python: $PYVER"

# pip
if ! command -v pip3 &> /dev/null; then
    echo "  WARNING: pip3 not found. Installing..."
    python3 -m ensurepip --upgrade
fi

# Homebrew (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew &> /dev/null; then
        echo "  WARNING: Homebrew not found. Install from https://brew.sh"
    else
        echo "  Homebrew: $(brew --version | head -1)"
    fi
fi

echo ""

# Step 1: Python dependencies for local analysis
echo "Step 1: Installing Python analysis dependencies..."
pip3 install --quiet pandas scipy numpy
echo "  Done."

# Step 2: Arena CLI
echo ""
echo "Step 2: Arena CLI"
if command -v arena &> /dev/null; then
    echo "  Already installed: $(arena --version 2>/dev/null || echo 'version unknown')"
else
    echo "  Downloading Arena CLI..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        curl -L https://arena.sentient.xyz/api/download/cli -o /tmp/arena
        chmod +x /tmp/arena
        echo "  Moving to /usr/local/bin (may need sudo)..."
        sudo mv /tmp/arena /usr/local/bin/arena
        echo "  Installed."
    else
        echo "  Non-macOS detected. Download manually from:"
        echo "  https://arena.sentient.xyz/api/download/cli"
    fi
fi

# Step 3: Daytona
echo ""
echo "Step 3: Daytona"
if command -v daytona &> /dev/null; then
    echo "  Already installed."
else
    echo "  Installing via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install daytonaio/tap/daytona
    else
        echo "  Homebrew not available. Install manually:"
        echo "  curl -sf -L https://download.daytona.io/daytona/install.sh | sudo bash"
    fi
fi

# Step 4: Environment variables
echo ""
echo "Step 4: Environment variables"
if [ -f .env ]; then
    echo "  .env file exists."
else
    if [ -f .env.example ]; then
        echo "  Copying .env.example to .env — EDIT WITH YOUR KEYS"
        cp .env.example .env
    else
        echo "  WARNING: No .env.example found."
    fi
fi

# Step 5: OfficeQA repo
echo ""
echo "Step 5: OfficeQA benchmark data"
OFFICEQA_DIR="${OFFICEQA_REPO:-$HOME/officeqa}"
if [ -d "$OFFICEQA_DIR" ]; then
    echo "  OfficeQA repo found at $OFFICEQA_DIR"
else
    echo "  Cloning OfficeQA repo to $OFFICEQA_DIR..."
    git clone https://github.com/databricks/officeqa.git "$OFFICEQA_DIR"
    echo "  Done. You may need to download the parsed TXT files separately (see SETUP.md)."
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Source your env: source .env  (or add to ~/.zshrc)"
echo "  3. Run: arena auth"
echo "  4. Run: arena init"
echo "  5. Inspect EVERYTHING arena init creates"
echo "  6. Record findings in notes/recon_findings.md"
echo "  7. Run baseline submission: arena submit"
echo "  8. Update SCRATCHPAD.md"
