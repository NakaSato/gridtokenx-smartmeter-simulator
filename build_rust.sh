#!/bin/bash
# Build the Rust Core extension using maturin
#
# Usage:
#   ./build_rust.sh          # Development build
#   ./build_rust.sh release  # Release build (optimized)
#   ./build_rust.sh wheel    # Build wheel for distribution

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUST_DIR="$SCRIPT_DIR/rust_core"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🦀 SmartMeter Core - Rust Extension Builder${NC}"
echo "=============================================="

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo -e "${YELLOW}⚠️  Rust not found. Installing via rustup...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

# Check Rust version
RUST_VERSION=$(rustc --version)
echo -e "${GREEN}✓${NC} Rust: $RUST_VERSION"

# Check if maturin is installed
if ! command -v maturin &> /dev/null; then
    echo -e "${YELLOW}⚠️  maturin not found. Installing...${NC}"
    pip install maturin
fi

MATURIN_VERSION=$(maturin --version)
echo -e "${GREEN}✓${NC} Maturin: $MATURIN_VERSION"

# Navigate to Rust directory
cd "$RUST_DIR"

# Parse command line arguments
BUILD_TYPE="${1:-develop}"

case "$BUILD_TYPE" in
    "develop"|"dev")
        echo -e "\n${BLUE}📦 Building development version...${NC}"
        maturin develop
        echo -e "${GREEN}✅ Development build complete!${NC}"
        echo -e "   Import with: ${YELLOW}import smartmeter_core${NC}"
        ;;
    
    "release")
        echo -e "\n${BLUE}🚀 Building release version (optimized)...${NC}"
        maturin develop --release
        echo -e "${GREEN}✅ Release build complete!${NC}"
        echo -e "   Import with: ${YELLOW}import smartmeter_core${NC}"
        ;;
    
    "wheel")
        echo -e "\n${BLUE}📦 Building wheel for distribution...${NC}"
        maturin build --release
        echo -e "${GREEN}✅ Wheel build complete!${NC}"
        echo -e "   Wheels are in: ${YELLOW}$RUST_DIR/target/wheels/${NC}"
        ls -la "$RUST_DIR/target/wheels/"*.whl 2>/dev/null || true
        ;;
    
    "clean")
        echo -e "\n${BLUE}🧹 Cleaning build artifacts...${NC}"
        cargo clean
        rm -rf "$RUST_DIR/target"
        echo -e "${GREEN}✅ Clean complete!${NC}"
        ;;
    
    "test")
        echo -e "\n${BLUE}🧪 Running Rust tests...${NC}"
        cargo test
        echo -e "${GREEN}✅ Tests complete!${NC}"
        ;;
    
    "bench")
        echo -e "\n${BLUE}📊 Running benchmarks...${NC}"
        cargo bench
        echo -e "${GREEN}✅ Benchmarks complete!${NC}"
        ;;
    
    "check")
        echo -e "\n${BLUE}🔍 Checking code...${NC}"
        cargo check
        cargo clippy -- -D warnings
        echo -e "${GREEN}✅ Check complete!${NC}"
        ;;
    
    *)
        echo -e "${RED}Unknown build type: $BUILD_TYPE${NC}"
        echo ""
        echo "Usage: $0 [develop|release|wheel|clean|test|bench|check]"
        echo ""
        echo "  develop  - Build and install for development (default)"
        echo "  release  - Build optimized version"
        echo "  wheel    - Build wheel for distribution"
        echo "  clean    - Clean build artifacts"
        echo "  test     - Run Rust tests"
        echo "  bench    - Run benchmarks"
        echo "  check    - Run cargo check and clippy"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"