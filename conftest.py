"""
Pytest configuration and fixtures for Chrome Extension testing with Playwright
"""
import pytest
import os
import tempfile
from pathlib import Path
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright, Playwright


# Path to your Chrome extension
# Can be overridden via EXTENSION_PATH environment variable
DEFAULT_EXTENSION_PATH = Path(__file__).parent / "chrome-extension"
EXTENSION_PATH = Path(os.getenv("EXTENSION_PATH", DEFAULT_EXTENSION_PATH))


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """
    Configure browser launch arguments for Chrome extension testing
    """
    return {
        "headless": False,  # Extensions require headed mode
        "args": [
            f"--disable-extensions-except={EXTENSION_PATH}",
            f"--load-extension={EXTENSION_PATH}",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ],
    }


@pytest.fixture(scope="session")
def browser_context_args():
    """
    Configure browser context arguments
    """
    return {
        "viewport": {"width": 1280, "height": 720},
        "locale": "en-US",
        "timezone_id": "America/New_York",
    }


# Override the default context fixture to use persistent context for extensions
@pytest.fixture(scope="function")
def context(playwright: Playwright):
    """
    Create a persistent browser context for each test with extension loaded
    This ensures the extension works properly across all pages
    """
    # Create a temporary directory for user data
    user_data_dir = tempfile.mkdtemp()
    
    print(f"\n[DEBUG] Launching browser with extension from: {EXTENSION_PATH}")
    
    # Launch persistent context with extension
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        args=[
            f"--disable-extensions-except={EXTENSION_PATH}",
            f"--load-extension={EXTENSION_PATH}",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ],
        viewport={"width": 1280, "height": 720},
        locale="en-US",
        timezone_id="America/New_York",
    )
    
    print(f"[DEBUG] Browser context created with {len(context.pages)} page(s)")
    
    yield context
    
    context.close()
    
    # Cleanup temp directory
    import shutil
    try:
        shutil.rmtree(user_data_dir)
    except:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """
    Get or create a page for each test
    Persistent context usually starts with a page already open
    """
    # Use existing page if available, otherwise create new one
    if context.pages:
        page = context.pages[0]
        print(f"[DEBUG] Using existing page: {page.url}")
    else:
        print(f"[DEBUG] Creating new page")
        page = context.new_page()
    
    yield page
    
    # Don't close the page - persistent context manages it
    # Just navigate to blank page for cleanup
    try:
        if not page.is_closed():
            page.goto("about:blank")
    except:
        pass  # Ignore errors during cleanup


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture screenshots on test failure
    """
    # Execute all other hooks to obtain the report object
    outcome = yield
    report = outcome.get_result()
    
    # Only capture screenshot for failed tests during call phase
    if report.when == "call" and report.failed:
        # Get the page fixture if available
        try:
            page = item.funcargs.get('page')
            if page and not page.is_closed():
                # Create screenshots directory
                screenshot_dir = Path("test-results/screenshots")
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate screenshot filename
                screenshot_path = screenshot_dir / f"{item.name}_{report.when}.png"
                
                # Take screenshot
                page.screenshot(path=str(screenshot_path))
                print(f"\n[SCREENSHOT] Saved to: {screenshot_path}")
                
                # Attach screenshot to HTML report
                if hasattr(report, 'extra'):
                    # Read screenshot and embed in HTML report
                    with open(screenshot_path, 'rb') as f:
                        screenshot_data = f.read()
                    
                    import base64
                    encoded = base64.b64encode(screenshot_data).decode('utf-8')
                    
                    html = f'<div><img src="data:image/png;base64,{encoded}" ' \
                           f'alt="screenshot" style="width:800px;height:auto;" /></div>'
                    
                    report.extra = getattr(report, 'extra', [])
                    report.extra.append(pytest_html.extras.html(html))
        except Exception as e:
            print(f"[WARNING] Could not capture screenshot: {e}")


# Add pytest-html import at the top if not present
try:
    import pytest_html
except ImportError:
    pass  # pytest-html not installed


@pytest.fixture(scope="function")
def extension_id(context: BrowserContext):
    """
    Get the extension ID from the loaded extension
    """
    # Navigate to chrome://extensions to get the extension ID
    # Note: This is a simplified approach
    # The actual extension ID is generated by Chrome
    background = None
    for ctx_page in context.pages:
        if ctx_page.url.startswith("chrome-extension://"):
            background = ctx_page
            break
    
    if background:
        # Extract extension ID from URL
        ext_id = background.url.split("/")[2]
        return ext_id
    
    return None


def pytest_configure(config):
    """
    Pytest configuration hook
    """
    # Create test-results directory and subdirectories if they don't exist
    test_results_dir = Path("test-results")
    test_results_dir.mkdir(exist_ok=True)
    
    screenshots_dir = test_results_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    
    traces_dir = test_results_dir / "traces"
    traces_dir.mkdir(exist_ok=True)
    
    print(f"[DEBUG] Test results will be saved to: {test_results_dir.absolute()}")
    
    # Validate that extension directory exists
    if not EXTENSION_PATH.exists():
        raise FileNotFoundError(
            f"Chrome extension not found at {EXTENSION_PATH}. "
            "Please ensure the chrome-extension directory exists."
        )


def pytest_collection_modifyitems(config, items):
    """
    Modify test items during collection
    """
    for item in items:
        # Add marker based on test name
        if "iframe" in item.nodeid.lower():
            item.add_marker(pytest.mark.iframe)
        if "extension" in item.nodeid.lower():
            item.add_marker(pytest.mark.extension)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_results():
    """
    Clean up old test results before running tests
    """
    # Yield to run tests first
    yield
    
    # Cleanup can be done here if needed
    # For now, we keep the results for CI/CD

