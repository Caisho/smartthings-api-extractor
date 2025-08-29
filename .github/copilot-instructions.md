# SmartThings API Extractor

SmartThings API Extractor is a Python tool for extracting and analyzing device history data from the SmartThings API. It retrieves paginated history data for specific SmartThings devices, processes it into structured formats (CSV/JSON), and provides specialized analysis for appliance cycles (particularly dryer cycles).

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap, Build, and Test the Repository

Use **uv** (recommended) for development:
```bash
# Install uv package manager if not available
pip install uv

# Create virtual environment with Python 3.10+
uv venv --python 3.10

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies including development tools
uv sync --group dev
# Time: <5 seconds for fresh installation, <1 second for subsequent runs
```

Alternative setup with **pip**:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package and dependencies
pip install -e .
# Time: ~10-15 seconds for fresh installation

# For development, manually install additional tools:
pip install pytest ruff vulture ipykernel ipython pytest-cov
```

### Development Commands and Timing

**Run tests:**
```bash
pytest
# Time: <1 second (currently no tests exist, framework is ready)
# Exit code 5 when no tests found - this is expected
```

**Code quality checks:**
```bash
# Format code
ruff format
# Time: <1 second
# NEVER CANCEL: Always completes quickly

# Check code style and issues
ruff check
# Time: <1 second
# NEVER CANCEL: Always completes quickly

# Check for dead/unused code
vulture src/
# Time: <1 second
# NEVER CANCEL: Always completes quickly
```

**Run the application:**
```bash
# Create .env file first (see Configuration section)
python src/scripts/extract_smartthings_history.py

# Or use the installed command (after pip install -e .)
extract-smartthings-history
# Time: Varies based on API data volume, typically 5-30 seconds for small datasets
```

## Configuration

Create a `.env` file in the project root with your SmartThings API credentials:

```env
BEARER_TOKEN=your_smartthings_bearer_token_here
LOCATION_ID=your_location_id_here
DEVICE_ID=your_device_id_here
TIMEZONE=America/New_York  # Optional, defaults to Asia/Singapore
```

**Required Environment Variables:**
- `BEARER_TOKEN`: Your SmartThings API bearer token (required)
- `LOCATION_ID`: The location ID containing your device (required)
- `DEVICE_ID`: The specific device ID to extract data from (required)
- `TIMEZONE`: Timezone for data processing (optional, defaults to "Asia/Singapore")

## Validation

**CRITICAL**: Always validate that ALL commands work before implementing changes. NEVER CANCEL long-running commands.

**Manual Application Testing:**
After making changes to the code, validate functionality by:

1. **Test development environment setup:**
   ```bash
   # Ensure virtual environment is activated
   source .venv/bin/activate  # or source venv/bin/activate
   
   # Verify all development tools are available
   which python ruff pytest vulture
   
   # Test basic imports work
   python -c "import src.scripts.extract_smartthings_history; print('✓ Import successful')"
   ```

2. **Create test credentials** (use `.env.example` as template):
   ```bash
   cp .env.example .env
   # Edit .env with real or test credentials
   ```

3. **Test basic execution** (without real API calls):
   ```bash
   # This should fail gracefully with authentication error, not crash
   python src/scripts/extract_smartthings_history.py
   # Expected: "ValueError: BEARER_TOKEN environment variable is required" if no .env
   ```

4. **Test with real credentials** (if available):
   - Run the script with valid SmartThings API credentials
   - Verify CSV and JSON output files are created with timestamps
   - Check console output shows extraction summary and data information
   - **Application runtime**: Varies based on API data volume, typically 5-30 seconds for small datasets

**Always run code quality checks before committing:**
```bash
ruff format && ruff check
# Both commands complete in <1 second. NEVER CANCEL.
```

## Project Structure

### Key Directories
```
src/
├── scripts/
│   ├── __init__.py
│   └── extract_smartthings_history.py  # Main application script
├── __init__.py
tests/
├── conftest.py
├── integration/
├── unit/
├── __init__.py
notebooks/  # Reserved for Jupyter notebooks (currently empty)
```

### Important Files
- `pyproject.toml`: Project configuration, dependencies, and tool settings
- `README.md`: Comprehensive project documentation
- `uv.lock`: Lock file for uv dependency management
- `.gitignore`: Excludes output files (*.csv, *.json), virtual environments

### Main Application
- **Entry point**: `src/scripts/extract_smartthings_history.py`
- **Installed command**: `extract-smartthings-history` (after pip install -e .)
- **Output files**: Creates timestamped CSV, JSON, and optional duration analysis files

## Common Tasks

### Development Environment Issues

**uv installation fails with network issues:**
```bash
# Fallback to pip installation
pip install uv
```

**Dependency group vs extras confusion:**
```bash
# Use --group for dependency groups (correct)
uv sync --group dev

# Do NOT use --extra (this will fail)
# uv sync --extra dev  # ❌ Wrong
```

### Code Quality Issues

**Current known linting issues in codebase:**
```bash
# These unused variables exist and should be fixed:
# src/scripts/extract_smartthings_history.py:286: unused variable 'power_on_event'
# src/scripts/extract_smartthings_history.py:358: unused variable 'tz_suffix'
```

**Formatting issues:**
```bash
# Several files need reformatting - run this before committing:
ruff format
```

### Application Usage

**Without SmartThings API credentials:**
- Application will fail with clear error message about missing environment variables
- This is expected behavior for validation

**With valid credentials:**
- Application extracts data from SmartThings API
- Creates timestamped output files in project root
- Displays extraction summary and data analysis

### Dependencies

**Runtime dependencies** (automatically installed):
- pandas>=2.3.1
- requests>=2.32.4
- python-dotenv>=1.0.0
- pytz>=2023.3

**Development tools** (install with --group dev):
- pytest>=8.4.1
- ruff>=0.12.4
- vulture>=2.14
- pytest-cov>=6.2.1
- ipykernel, ipython (for notebook development)

## Critical Timing and Performance Notes

**NEVER CANCEL any command listed below. All commands complete quickly:**

- `uv venv --python 3.10`: <1 second always
- `uv sync --group dev`: <5 seconds maximum (fresh), <1 second (subsequent)
- `pip install -e .`: 10-15 seconds maximum  
- `ruff check`: <1 second always
- `ruff format`: <1 second always
- `vulture src/`: <1 second always
- `pytest`: <1 second (when no tests exist)

**Application execution time varies:**
- Without credentials: Instant failure with clear error message
- With valid credentials: 5-30 seconds depending on data volume from SmartThings API

**Memory and Storage:**
- Virtual environment: ~200MB disk space
- Output files: Variable size based on data extracted (typically <10MB)

## Troubleshooting Common Issues

**"uv sync --extra dev" fails:**
- Use `--group dev` instead of `--extra dev`
- The project uses dependency groups, not optional dependencies

**"pytest" command not found:**
- Ensure virtual environment is activated: `source .venv/bin/activate`
- Verify development dependencies are installed: `uv sync --group dev`

**Import errors when running Python scripts:**
- Check that virtual environment is activated
- Verify all dependencies are installed
- Test with: `python -c "import pandas, requests, pytz; print('✓ Dependencies OK')"`

**Application crashes immediately:**
- Expected if no .env file exists
- Expected if BEARER_TOKEN, LOCATION_ID, or DEVICE_ID environment variables are missing
- Check error message for specific missing variable

**Linting failures:**
- Known issues exist in the codebase (documented in instructions)
- Run `ruff check` to see current issues
- Run `ruff format` to fix formatting automatically

## Repository Info from Common Commands

### Repository Structure
```bash
ls -la
# Key files: pyproject.toml, README.md, uv.lock, .gitignore
# Key directories: src/, tests/, notebooks/, .vscode/
```

### Package Configuration
```bash
cat pyproject.toml
# Python 3.10+ required
# Uses dependency groups instead of extras
# Configured entry point: extract-smartthings-history
# Includes ruff, pytest, and coverage configuration
```

### Git Status
```bash
git status
# Project excludes *.csv, *.json output files
# Virtual environments (.venv/, venv/, test_venv/) are ignored
# No build artifacts are tracked
```