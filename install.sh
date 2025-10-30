# CStarX v2.0 - Installation Script

set -e

echo "🚀 Installing CStarX v2.0..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Check Rust installation
if ! command -v rustc &> /dev/null; then
    echo "📦 Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source ~/.cargo/env
else
    echo "✅ Rust is already installed"
fi

# Check clang installation
if ! command -v clang &> /dev/null; then
    echo "📦 Installing clang..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install -y clang llvm
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install llvm
    else
        echo "❌ Please install clang manually for your OS"
        exit 1
    fi
else
    echo "✅ clang is already installed"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -e .

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Create example project
echo "📁 Creating example project..."
python -c "from cstarx.examples.simple_project import create_example_project; create_example_project('examples/simple_project')"

# Create output directory
mkdir -p output

echo "🎉 Installation complete!"
echo ""
echo "Quick Start:"
echo "  1. Copy env.example to .env and configure your API keys"
echo "  2. Run: cstarx translate input/01-Primary --output output/01-Primary"
echo "  3. Or start the web interface: python -m src.api"
echo ""
echo "Documentation: https://docs.cstarx.dev"
echo "Issues: https://github.com/cstarx/cstarx-v2/issues"
