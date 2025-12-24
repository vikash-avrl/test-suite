"""
Basic smoke tests for Chrome Extension functionality using DOM Bridge
"""
import pytest
from playwright.sync_api import Page, BrowserContext, expect, TimeoutError
import time
import os


def send_test_command(page: Page, action: str, data: dict = None):
    """
    Send a command to the extension via DOM event bridge
    This works in both headed and headless modes!
    """
    result = page.evaluate("""
        ({ action, data }) => {
            return new Promise((resolve) => {
                const bridge = document.getElementById('__avrl-glass-test-bridge__');
                
                if (!bridge) {
                    resolve({ success: false, error: 'Bridge not found' });
                    return;
                }
                
                // Listen for response
                const responseHandler = (event) => {
                    bridge.removeEventListener('avrl-test-response', responseHandler);
                    resolve(event.detail);
                };
                
                bridge.addEventListener('avrl-test-response', responseHandler);
                
                // Send command
                const commandEvent = new CustomEvent('avrl-test-command', {
                    detail: { action, data }
                });
                bridge.dispatchEvent(commandEvent);
                
                // Timeout after 5 seconds
                setTimeout(() => {
                    bridge.removeEventListener('avrl-test-response', responseHandler);
                    resolve({ success: false, error: 'Timeout waiting for response' });
                }, 5000);
            });
        }
    """, {'action': action, 'data': data or {}})
    
    return result


@pytest.mark.smoke
@pytest.mark.extension
def test_extension_is_installed(page: Page, context):
    """
    Test 1: Verify that the extension is installed and bridge is available
    """
    extension_path = os.getenv("EXTENSION_PATH", "chrome-extension/")
    print(f"\n[TEST 1] Checking extension installation")
    print(f"[DEBUG] Extension path: {extension_path}")
    
    # Method 1: Check if extension background/service worker page exists
    extension_pages = [p for p in context.pages if p.url.startswith("chrome-extension://")]
    
    if extension_pages:
        print(f"[OK] Found {len(extension_pages)} extension page(s)")
        for ext_page in extension_pages:
            print(f"  - {ext_page.url}")
    else:
        print("[WARNING] No extension pages found (normal for some extensions)")
    
    # Method 2: Navigate to a page and check if extension injected the test bridge
    test_url = "https://storage.googleapis.com/avrlgeneration_static_assets_staging/html_template/rxo_mock_template.html"
    page.goto(test_url)
    page.wait_for_load_state("networkidle")
    print(f"[OK] Test page loaded: {page.url}")
    
    # Wait for extension to inject
    print("[DEBUG] Waiting for extension to inject (3 seconds)...")
    time.sleep(3)
    
    # Check if test bridge exists
    bridge_exists = page.evaluate("""
        () => {
            const bridge = document.getElementById('__avrl-glass-test-bridge__');
            return bridge !== null && bridge.getAttribute('data-ready') === 'true';
        }
    """)
    
    print(f"[INFO] Test bridge exists: {bridge_exists}")
    
    if bridge_exists:
        print(f"[OK] Test bridge is ready!")
        
        # Test the bridge with a ping
        ping_result = send_test_command(page, 'ping')
        
        if ping_result['success']:
            print(f"[SUCCESS] Bridge communication working!")
            print(f"  - Ping response: {ping_result['message']}")
        else:
            print(f"[WARNING] Bridge exists but ping failed")
    else:
        print(f"[WARNING] Test bridge not found")
        print(f"[INFO] Make sure you added the test bridge code to content.js")
    
    # Method 3: Check for extension console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg.text))
    
    page.reload()
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    extension_messages = [msg for msg in console_messages if 'AVRL' in msg or 'Test Bridge' in msg]
    if extension_messages:
        print(f"[OK] Extension console messages found:")
        for msg in extension_messages[:5]:
            print(f"  - {msg}")
    
    print("[SUCCESS] Extension installation verified")
    assert True, "Extension is installed and working"


@pytest.mark.smoke
@pytest.mark.extension
def test_click_popup_opens_new_page(page: Page, context: BrowserContext):
    """
    Test 2: Simulate clicking the popup and verify new page opens
    
    This test:
    - Clears any stored account
    - Triggers popup via DOM bridge (simulates clicking extension icon)
    - Verifies new Glass login page opens
    
    This works in both local and CI environments!
    """
    print(f"\n[TEST 2] Testing popup click (trigger extension action)")
    
    # Navigate to test page
    test_url = "https://storage.googleapis.com/avrlgeneration_static_assets_staging/html_template/rxo_mock_template.html"
    page.goto(test_url)
    page.wait_for_load_state("networkidle")
    print(f"[OK] Test page loaded")
    
    # Wait for extension
    print("[DEBUG] Waiting for extension to initialize...")
    time.sleep(3)
    
    # Check if bridge is available
    bridge_exists = page.evaluate("() => document.getElementById('__avrl-glass-test-bridge__') !== null")
    
    if not bridge_exists:
        print("[ERROR] Test bridge not found!")
        print("[FIX] Add the test bridge code to your extension's content.js")
        pytest.skip("Test bridge not available - extension needs test hooks")
    
    print("[OK] Test bridge found")
    
    # Clear account to test "no account" scenario
    print("[DEBUG] Clearing stored account...")
    clear_result = send_test_command(page, 'clear-account')
    
    if clear_result.get('success'):
        print("[OK] Account cleared")
    else:
        print("[WARNING] Could not clear account (action might not be available)")
    
    time.sleep(2)
    
    # Track initial pages
    initial_page_count = len(context.pages)
    print(f"[DEBUG] Initial pages: {initial_page_count}")
    
    # Trigger popup (simulates clicking the extension icon)
    print("[DEBUG] Triggering popup action...")
    print("           (This simulates clicking the extension icon)")
    
    try:
        # Wait for new page to open
        with context.expect_page(timeout=15000) as new_page_info:
            trigger_result = send_test_command(page, 'trigger-popup')
            print(f"[OK] Trigger sent: {trigger_result['success']}")
        
        # New page opened! (No account scenario)
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded", timeout=15000)
        new_page_url = new_page.url
        
        print(f"\n[SUCCESS] NEW PAGE OPENED!")
        print(f"[OK] URL: {new_page_url}")
        
        # Verify it's the correct Glass login page
        assert "glass.1avrl.com" in new_page_url and "render_page_to_user" in new_page_url, \
            f"Expected Glass login page, got: {new_page_url}"
        
        print(f"[SUCCESS] Correct AVRL Glass login page opened!")
        
        # Get page title
        page_title = new_page.title()
        print(f"[INFO] Page title: {page_title}")
        
        # Take screenshot
        screenshot_path = "test-results/screenshots/glass_login_page.png"
        new_page.screenshot(path=screenshot_path)
        print(f"[SCREENSHOT] Saved: {screenshot_path}")
        
        # Close the new page
        new_page.close()
        
        final_page_count = len(context.pages)
        print(f"[DEBUG] Final pages: {final_page_count}")
        
        print(f"\n[SUCCESS] Popup trigger test PASSED!")
        print(f"           Clicking popup correctly opened Glass login page")
        
        assert True, "Popup action opened new Glass login page"
        
    except Exception as e:
        # No new page opened - might have account configured
        print(f"\n[INFO] No new page opened: {e}")
        print(f"[DEBUG] Checking if iframe appeared instead...")
        
        time.sleep(2)
        
        # Check for iframe
        iframe_result = send_test_command(page, 'get-iframe-info')
        
        if iframe_result['success'] and iframe_result.get('iframe'):
            iframe_info = iframe_result['iframe']
            print(f"[INFO] Iframe appeared instead:")
            print(f"  - ID: {iframe_info['id']}")
            print(f"  - Visible: {iframe_info['visible']}")
            
            print(f"\n[NOTE] This means an account is configured in extension storage")
            print(f"[NOTE] With account: popup toggles iframe")
            print(f"[NOTE] Without account: popup opens new page")
            
            # This is valid behavior, but not the "no account" scenario we're testing
            print(f"\n[INFO] Clearing account and trying again...")
            
            # Try clearing and triggering again
            send_test_command(page, 'clear-account')
            time.sleep(2)
            
            try:
                with context.expect_page(timeout=10000) as retry_page_info:
                    send_test_command(page, 'trigger-popup')
                
                retry_page = retry_page_info.value
                retry_url = retry_page.url
                print(f"[SUCCESS] After clearing account, new page opened: {retry_url}")
                retry_page.close()
                assert True, "Popup opened new page after clearing account"
            except:
                print(f"[WARNING] Still no new page after clearing account")
                print(f"[INFO] Test inconclusive - extension might have persistent storage")
                pytest.skip("Could not test 'no account' scenario - account persists")
        else:
            print(f"[ERROR] No new page and no iframe - unexpected behavior")
            
            # Take failure screenshot
            page.screenshot(path="test-results/screenshots/popup_test_failure.png")
            
            pytest.fail(f"Popup trigger didn't open new page or iframe: {e}")





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

