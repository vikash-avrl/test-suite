# 🧪 Chrome Extension Testing Suite with Playwright (Python)

A comprehensive testing framework for Chrome extensions that inject iframes into web pages. Built with Playwright and pytest, fully integrated with GitHub Actions for CI/CD.

> **⭐ New to this project?** Start with **[COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)** for step-by-step setup!

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Point to your extension
export EXTENSION_PATH=/path/to/your/chrome-extension

# 3. Validate setup
python validate_setup.py

# 4. Run tests
pytest tests/ -v
```

**That's it!** For detailed instructions, see [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md).

---

## 📋 Documentation Quick Links

- 🎯 **[START_HERE.md](START_HERE.md)** - Complete overview and next steps
- 📖 **[COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)** - Step-by-step setup guide
- ⚡ **[QUICKSTART.md](QUICKSTART.md)** - Fast setup for your use case
- 🤖 **[GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)** - CI/CD detailed guide
- 💬 **[ANSWER.md](ANSWER.md)** - Direct answer to "How to pass extension in GitHub Actions?"
- 📊 **[FLOW_DIAGRAM.md](FLOW_DIAGRAM.md)** - Visual workflow diagrams
- 📚 **[INDEX.md](INDEX.md)** - Complete documentation index

---

## 📋 Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Chrome Extension Setup](#chrome-extension-setup)
- [GitHub Actions Setup](#github-actions-setup)
- [Writing Tests](#writing-tests)
- [Configuration](#configuration)

## ✨ Features

- ✅ **Python-based testing** with pytest and Playwright
- ✅ **Chrome extension support** with real browser testing
- ✅ **Iframe testing** capabilities
- ✅ **GitHub Actions integration** for automated CI/CD
- ✅ **Comprehensive test reports** with HTML output
- ✅ **Parallel test execution** support
- ✅ **Screenshot and video recording** on failures

## 🔧 Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- Your Chrome extension code

## 📦 Installation

### Local Setup

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd test_suite_for_glass
```

2. **Create virtual environment (recommended):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers:**
```bash
playwright install chromium
```

## 📁 Project Structure

```
test_suite_for_glass/
├── tests/
│   ├── test_basic.py          # Basic smoke tests
│   ├── test_iframe.py         # Iframe-specific tests
│   └── test_integration.py    # Integration tests
├── .github/
│   └── workflows/
│       └── test.yml           # GitHub Actions workflow
├── conftest.py                # Pytest configuration and fixtures
├── pytest.ini                 # Pytest settings
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🚀 Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run with verbose output:
```bash
pytest tests/ -v
```

### Run specific test file:
```bash
pytest tests/test_iframe.py -v
```

### Run tests by marker:
```bash
# Run only smoke tests
pytest tests/ -m smoke

# Run only iframe tests
pytest tests/ -m iframe

# Run integration tests
pytest tests/ -m integration
```

### Run with HTML report:
```bash
pytest tests/ --html=test-results/report.html --self-contained-html
```

### Run in headed mode (see browser):
```bash
# Headed mode is default for extension testing
pytest tests/ -v
```

### Run specific test:
```bash
pytest tests/test_iframe.py::test_iframe_injection -v
```

## 🔌 Chrome Extension Setup

### Option 1: Extension in Repository

If your Chrome extension is in the same repository:

1. **Place your extension in a folder** (e.g., `my-extension/`)
2. **Update the path in conftest.py** or use environment variable:

```bash
# Windows
set EXTENSION_PATH=C:\path\to\your\extension
pytest tests/

# Linux/Mac
export EXTENSION_PATH=/path/to/your/extension
pytest tests/
```

### Option 2: Extension in Separate Repository

If your extension is in a different repo, you have two options:

**A. Git Submodule:**
```bash
git submodule add <extension-repo-url> my-extension
```

**B. Clone during CI (see GitHub Actions section)**

## 🤖 GitHub Actions Setup

### Step 1: Update Workflow File

Edit `.github/workflows/test.yml` and set your extension path:

```yaml
- name: Run tests with extension from repo
  env:
    EXTENSION_PATH: ${{ github.workspace }}/YOUR-EXTENSION-FOLDER
  run: |
    pytest tests/ -v --html=test-results/report.html --self-contained-html
```

### Step 2: Choose Your Strategy

#### **Strategy A: Extension in Same Repo**

```yaml
# In .github/workflows/test.yml
- name: Checkout repository
  uses: actions/checkout@v4

- name: Run tests
  env:
    EXTENSION_PATH: ${{ github.workspace }}/my-extension
  run: pytest tests/ -v
```

#### **Strategy B: Extension in Different Repo**

```yaml
# In .github/workflows/test.yml
- name: Checkout test repository
  uses: actions/checkout@v4

- name: Checkout Chrome extension
  uses: actions/checkout@v4
  with:
    repository: your-org/your-extension-repo
    path: my-extension
    token: ${{ secrets.GITHUB_TOKEN }}

- name: Run tests
  env:
    EXTENSION_PATH: ${{ github.workspace }}/my-extension
  run: pytest tests/ -v
```

#### **Strategy C: Extension Needs Building**

```yaml
- name: Checkout extension
  uses: actions/checkout@v4
  with:
    path: my-extension

- name: Build extension
  run: |
    cd my-extension
    npm install
    npm run build

- name: Run tests
  env:
    EXTENSION_PATH: ${{ github.workspace }}/my-extension/dist
  run: pytest tests/ -v
```

### Step 3: Set Up Secrets (if needed)

If your extension repo is private:

1. Go to your test repo → Settings → Secrets and variables → Actions
2. Add `PAT_TOKEN` (Personal Access Token) with repo access
3. Update workflow:

```yaml
- name: Checkout Chrome extension
  uses: actions/checkout@v4
  with:
    repository: your-org/your-extension-repo
    path: my-extension
    token: ${{ secrets.PAT_TOKEN }}
```

## ✍️ Writing Tests

### Basic Test Structure

```python
import pytest
from playwright.sync_api import Page, expect

def test_my_feature(page: Page):
    # Navigate to page
    page.goto("https://example.com")
    
    # Your test logic here
    expect(page.locator("#my-element")).to_be_visible()
```

### Testing Iframe Injection

```python
@pytest.mark.iframe
def test_iframe_appears(page: Page):
    page.goto("https://example.com")
    
    # Wait for your extension to inject iframe
    page.wait_for_selector("#your-iframe-id", timeout=5000)
    
    # Verify iframe exists
    iframe = page.locator("#your-iframe-id")
    expect(iframe).to_be_visible()
```

### Interacting with Iframe Content

```python
def test_iframe_content(page: Page):
    page.goto("https://example.com")
    page.wait_for_selector("#extension-iframe")
    
    # Access iframe content
    iframe = page.frame_locator("#extension-iframe")
    
    # Interact with elements inside iframe
    expect(iframe.locator("h1")).to_contain_text("Expected Text")
```

## ⚙️ Configuration

### Environment Variables

- `EXTENSION_PATH`: Path to your Chrome extension directory
- `CI`: Set to `true` in CI environments (automatic in GitHub Actions)

### Pytest Markers

Available markers in `pytest.ini`:
- `@pytest.mark.smoke`: Quick smoke tests
- `@pytest.mark.iframe`: Iframe-specific tests
- `@pytest.mark.extension`: Extension behavior tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Long-running tests

### conftest.py Customization

Edit `conftest.py` to customize:
- Browser launch arguments
- Extension path
- Test fixtures
- Setup/teardown logic

## 📊 Test Reports

After running tests, reports are generated:

- **HTML Report**: `test-results/report.html`
- **JSON Report**: `test-results/results.json`
- **JUnit XML**: `test-results/junit.xml`

In GitHub Actions, reports are uploaded as artifacts.

## 🐛 Troubleshooting

### Extension not loading
- Verify `EXTENSION_PATH` is correct
- Check extension has valid `manifest.json`
- Ensure Chromium is installed: `playwright install chromium`

### Tests failing in CI but passing locally
- Check extension path in GitHub Actions workflow
- Verify all dependencies are installed
- Check if extension needs building step

### Iframe not found
- Increase timeout in `page.wait_for_selector()`
- Verify extension actually injects iframe
- Check console logs: `page.on("console", lambda msg: print(msg.text))`

## 📝 Example Workflow

Here's the complete flow for your use case:

1. **You push changes to your extension** (template updates)
2. **GitHub Actions automatically triggers**
3. **Workflow checks out both repos** (tests + extension)
4. **Installs Python dependencies** and Playwright
5. **Runs all tests** with your extension loaded
6. **Generates reports** and uploads artifacts
7. **Comments on PR** with test results

## 🔗 Useful Links

- [Playwright Python Docs](https://playwright.dev/python/)
- [pytest Documentation](https://docs.pytest.org/)
- [Chrome Extension Manifest V3](https://developer.chrome.com/docs/extensions/mv3/)

## 📄 License

[Your License Here]

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

---

**Happy Testing! 🎉**

