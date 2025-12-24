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
    
    # Detect if running in CI environment
    is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
    
    print(f"\n[DEBUG] Launching browser with extension from: {EXTENSION_PATH}")
    print(f"[DEBUG] Running in CI mode: {is_ci}")
    
    # Launch persistent context with extension
    # Note: Chrome extensions have LIMITED support in old headless mode
    # Using new headless mode (--headless=new) for better extension support
    launch_args = [
        f"--disable-extensions-except={EXTENSION_PATH}",
        f"--load-extension={EXTENSION_PATH}",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-software-rasterizer",
    ]
    
    # In CI, try using "new" headless mode which supports extensions better
    if is_ci:
        print("[DEBUG] Using new headless mode for better extension support")
        # New headless mode via chrome_type instead of headless=True
        launch_args.append("--headless=new")
        headless_mode = False  # Let Chrome handle headless via flag
    else:
        headless_mode = False
    
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=headless_mode,
        args=launch_args,
        viewport={"width": 1280, "height": 720},
        locale="en-US",
        timezone_id="America/New_York",
        ignore_default_args=["--disable-extensions"],
    )
    
    print(f"[DEBUG] Browser context created with {len(context.pages)} page(s)")
    
    # Verify extension is loaded by checking for extension pages
    extension_pages = [p for p in context.pages if p.url.startswith("chrome-extension://")]
    if extension_pages:
        print(f"[DEBUG] Found {len(extension_pages)} extension page(s):")
        for ext_page in extension_pages:
            print(f"  - {ext_page.url}")
    else:
        print(f"[WARNING] No extension pages found - extension may not be loaded!")
        print(f"[INFO] Extension path: {EXTENSION_PATH}")
        print(f"[INFO] Extension exists: {EXTENSION_PATH.exists()}")
        if EXTENSION_PATH.exists():
            manifest_path = EXTENSION_PATH / "manifest.json"
            print(f"[INFO] manifest.json exists: {manifest_path.exists()}")
    
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
    # Setup API route interception at CONTEXT level (works for all pages including iframes)
    template_url = os.getenv(
        "TEMPLATE_FILE_PATH",
        "file:///C:/Users/vikas/OneDrive/Desktop/avrlglassgit/templates/avrl_glass_display_pane/template0.html"
    )
    
    # Check if running in CI
    is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
    
    if not is_ci:
        # Only intercept locally, not in CI
        print(f"[DEBUG] Setting up API interception for glass_template (context level)")
        print(f"[DEBUG] Will serve content from: {template_url}")
        
        def handle_route(route):
            try:
                print(f"[INTERCEPT] Caught request: {route.request.url}")
                
                # Read the local file content
                file_path = template_url.replace("file:///", "").replace("file://", "")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"[INTERCEPT] Serving local file ({len(content)} bytes)")
                
                # Return 200 with actual content (not redirect!)
                route.fulfill(
                    status=200,
                    content_type='text/html; charset=utf-8',
                    body=content,
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, OPTIONS',
                        'Access-Control-Allow-Headers': '*'
                    }
                )
            except Exception as e:
                print(f"[ERROR] Interception failed: {e}")
                import traceback
                traceback.print_exc()
                route.continue_()
        
        # Intercept at CONTEXT level (catches all frames/iframes)
        context.route("https://glass.1avrl.com/glass_template", handle_route)
        context.route("https://glass.1avrl.com/glass_template*", handle_route)
        print(f"[DEBUG] Route interception activated on context")
    else:
        print(f"[DEBUG] Running in CI - no API interception")
    
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
    Hook to capture screenshots on test failure (saved to test-results/screenshots/)
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
        except Exception as e:
            print(f"[WARNING] Could not capture screenshot: {e}")


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
    import os
    
    # Create test-results directory and subdirectories using os.makedirs for better compatibility
    os.makedirs("test-results/screenshots", exist_ok=True)
    os.makedirs("test-results/traces", exist_ok=True)
    
    print(f"[DEBUG] Test results directory created at: {Path('test-results').absolute()}")
    
    # Validate that extension directory exists
    if not EXTENSION_PATH.exists():
        raise FileNotFoundError(
            f"Chrome extension not found at {EXTENSION_PATH}. "
            "Please ensure the chrome-extension directory exists."
        )





# Global flag to track if any test has failed
_test_failed = False


def pytest_runtest_makereport(item, call):
    """
    Hook to track test failures and mark remaining tests
    """
    global _test_failed
    
    if call.when == "call":
        if call.excinfo is not None:
            # A test has failed
            _test_failed = True


def pytest_runtest_setup(item):
    """
    Hook called before each test setup
    Skip remaining tests if a previous test failed
    """
    global _test_failed
    
    if _test_failed:
        pytest.skip(f"Skipping due to previous test failure (fail-fast mode)")


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

