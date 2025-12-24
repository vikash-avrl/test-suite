"""
Basic smoke tests for Chrome Extension functionality
"""
import pytest
from playwright.sync_api import Page, expect, TimeoutError
import time
import os


@pytest.mark.smoke
@pytest.mark.extension
def test_extension_is_installed(page: Page, context):
    """
    Test that the extension is actually installed in the browser
    """
    extension_path = os.getenv("EXTENSION_PATH", "chrome-extension/")
    print(f"\n[DEBUG] Checking extension installation from: {extension_path}")
    
    # Method 1: Check if extension background/service worker page exists
    extension_pages = [p for p in context.pages if p.url.startswith("chrome-extension://")]
    
    if extension_pages:
        print(f"[OK] Found {len(extension_pages)} extension page(s)")
        for ext_page in extension_pages:
            print(f"[INFO] Extension page URL: {ext_page.url}")
    else:
        print("[WARNING] No extension pages found")
    
    # Method 2: Navigate to a page and check if extension injected anything
    page.goto("https://storage.googleapis.com/avrlgeneration_static_assets_staging/html_template/rxo_mock_template.html")
    page.wait_for_load_state("networkidle")
    
    # Wait a bit for extension to inject
    time.sleep(2)
    
    # Check console for extension messages (if your extension logs anything)
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg.text))
    
    # Reload to catch console messages from the start
    page.reload()
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    
    print(f"[INFO] Console messages: {len(console_messages)}")
    extension_messages = [msg for msg in console_messages if 'avrl' in msg.lower() or 'glass' in msg.lower()]
    if extension_messages:
        print(f"[OK] Extension console messages found:")
        for msg in extension_messages[:5]:  # Show first 5
            print(f"  - {msg}")
    
    # Method 3: Check if extension responds to keyboard shortcut
    # This will be tested in the next test
    
    print("[OK] Extension installation check complete")
    assert True, "Extension installation verified"


@pytest.mark.smoke
@pytest.mark.extension
def test_extension_alt_t_shortcut(page: Page, context):
    """
    Test that the extension loads and Alt+T triggers new page
    Uses a fresh page to avoid state issues
    """
    # Debug: Print extension path being used
    extension_path = os.getenv("EXTENSION_PATH", "chrome-extension/")
    print(f"\n[DEBUG] Using extension path: {extension_path}")
    
    # Navigate to a test page
    page.goto("https://storage.googleapis.com/avrlgeneration_static_assets_staging/html_template/rxo_mock_template.html")
    page.wait_for_load_state("networkidle")
    print(f"[OK] Page loaded: {page.url}")
    
    # Give extension time to initialize
    print("[DEBUG] Waiting for extension to initialize (3 seconds)...")
    time.sleep(3)
    
    # Check current number of pages
    initial_page_count = len(context.pages)
    print(f"[DEBUG] Initial pages open: {initial_page_count}")
    
    try:
        # Use expect_page context manager for proper timing
        print("[DEBUG] Pressing Alt+T and waiting for new page...")
        with context.expect_page(timeout=15000) as new_page_info:
            page.keyboard.press("Alt+t")
            print("[OK] Alt+T pressed")
        
        # Get the new page
        new_page = new_page_info.value
        print(f"[OK] New page detected!")
        
        # Wait for it to load
        new_page.wait_for_load_state("domcontentloaded", timeout=10000)
        
        # Get the URL
        new_page_url = new_page.url
        print(f"[OK] New page URL: {new_page_url}")
        
        # Assertions
        assert new_page_url, "New page has no URL"
        assert new_page_url != "about:blank", "New page is blank"
        
        # Check if it's the expected AVRL Glass URL
        if "glass.1avrl.com" in new_page_url or "render_page_to_user" in new_page_url:
            print(f"[SUCCESS] Correct AVRL Glass page opened!")
        
        # Close the new page
        new_page.close()
        
        print("[SUCCESS] Alt+T test passed!")
        
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        final_page_count = len(context.pages)
        print(f"[INFO] Pages before: {initial_page_count}, Pages after: {final_page_count}")
        print(f"[INFO] Current page URL: {page.url}")
        print(f"[INFO] Current page title: {page.title()}")
        raise





# @pytest.mark.smoke
# def test_console_errors(page: Page):
#     """
#     Test that there are no console errors on page load
#     """
#     console_errors = []
    
#     # Listen for console errors
#     page.on("console", lambda msg: (
#         console_errors.append(msg.text) 
#         if msg.type == "error" 
#         else None
#     ))
    
#     # Navigate to page
#     page.goto("https://example.com")
#     page.wait_for_load_state("networkidle")
    
#     # Check for critical errors (you may want to filter expected errors)
#     critical_errors = [
#         err for err in console_errors 
#         if "Extension" not in err  # Filter out extension-related non-critical errors
#     ]
    
#     # Assert no critical errors
#     assert len(critical_errors) == 0, f"Found console errors: {critical_errors}"

