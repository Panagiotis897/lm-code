#!/bin/bash
set -e

# Colors for output
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BLUE}Installing lmcode...${RESET}"

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo -e "${RED}Error: pip is not installed.${RESET}"
    echo "Please install pip and try again."
    exit 1
fi

# Install the package
echo -e "${YELLOW}Installing package from PyPI...${RESET}"
pip install --upgrade lmcode

# Create shortcut in ~/.local/bin if it exists and is in PATH
if [[ -d "$HOME/.local/bin" && "$PATH" == *"$HOME/.local/bin"* ]]; then
    echo -e "${YELLOW}Creating 'lmcode' shortcut...${RESET}"
    cat > "$HOME/.local/bin/lmcode" << 'EOF'
#!/bin/bash
python -m lmcode_cli "$@"
EOF
    chmod +x "$HOME/.local/bin/lmcode"
fi

echo -e "${GREEN}Installation complete!${RESET}"
echo ""
echo -e "${BLUE}To get started:${RESET}"
echo -e "1. Set up your API key: ${YELLOW}lmcode setup${RESET}"
echo -e "2. Start using lmcode: ${YELLOW}lmcode${RESET}"
echo ""
echo -e "For more information, visit: https://github.com/Panagiotis897/lm-code"
