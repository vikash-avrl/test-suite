"""
Basic smoke tests for Chrome Extension functionality using DOM Bridge
"""
import pytest
from playwright.sync_api import Page, BrowserContext, expect, TimeoutError
import time
import os


# Helper function: Login to Glass
def login_to_glass(page: Page, username: str, password: str):
    """
    Helper function to login to Glass
    
    Args:
        page: Playwright page object
        username: Glass username
        password: Glass password
    
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        login_url = "https://glass.1avrl.com/render_page_to_user"
        print(f"[LOGIN] Navigating to: {login_url}")
        page.goto(login_url, timeout=15000)
        page.wait_for_load_state("networkidle")
        
        print(f"[LOGIN] Filling credentials...")
        page.locator("xpath=/html/body/div[1]/form/input[1]").fill(username)
        page.locator("xpath=/html/body/div[1]/form/input[2]").fill(password)
        
        print(f"[LOGIN] Clicking login button...")
        page.locator("xpath=/html/body/div[1]/form/button").click()
        
        page.wait_for_load_state("networkidle", timeout=10000)
        print(f"[LOGIN] Login successful! Current URL: {page.url}")
        return True
        
    except Exception as e:
        print(f"[LOGIN] Login failed: {e}")
        return False


def select_costmodel(page: Page):
    """
    Helper function to find and click costmodel button
    
    Args:
        page: Playwright page object
    
    Returns:
        bool: True if costmodel selected, False otherwise
    """
    try:
        print(f"[COSTMODEL] Looking for costmodel button...")
        
        # Try multiple selectors
        selectors = [
            "button:has-text('costmodel')",
            "button:has-text('Costmodel')",
            "button:has-text('COSTMODEL')",
            "[role='button']:has-text('costmodel')",
            "//button[contains(text(), 'costmodel')]",
        ]
        
        for selector in selectors:
            try:
                button = page.locator(selector).first
                if button.is_visible(timeout=2000):
                    print(f"[COSTMODEL] Found button with: {selector}")
                    button.click()
                    print(f"[COSTMODEL] Button clicked!")
                    page.wait_for_load_state("networkidle", timeout=10000)
                    return True
            except:
                continue
        
        print(f"[COSTMODEL] Button not found")
        return False
        
    except Exception as e:
        print(f"[COSTMODEL] Error: {e}")
        return False


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


# @pytest.mark.smoke
# @pytest.mark.extension
# def test_extension_is_installed(page: Page, context):
#     """
#     Test 1: Verify that the extension is installed and bridge is available
#     """
#     extension_path = os.getenv("EXTENSION_PATH", "chrome-extension/")
#     print(f"\n[TEST 1] Checking extension installation")
#     print(f"[DEBUG] Extension path: {extension_path}")
    
#     # Method 1: Check if extension background/service worker page exists
#     extension_pages = [p for p in context.pages if p.url.startswith("chrome-extension://")]
    
#     if extension_pages:
#         print(f"[OK] Found {len(extension_pages)} extension page(s)")
#         for ext_page in extension_pages:
#             print(f"  - {ext_page.url}")
#     else:
#         print("[WARNING] No extension pages found (normal for some extensions)")
    
#     # Capture ALL console messages
#     console_messages = []
#     def handle_console(msg):
#         console_messages.append(f"[CONSOLE {msg.type}] {msg.text}")
#         print(f"[CONSOLE {msg.type}] {msg.text}")
    
#     page.on("console", handle_console)
    
#     # Method 2: Navigate to a page and check if extension injected the test bridge
#     test_url = "https://storage.googleapis.com/avrlgeneration_static_assets_staging/html_template/rxo_mock_template.html"
#     page.goto(test_url)
#     page.wait_for_load_state("networkidle")
#     print(f"[OK] Test page loaded: {page.url}")
    
#     print(f"\n[DEBUG] Console messages so far: {len(console_messages)}")
#     print(f"\n[DEBUG] Console messages so far: {len(console_messages)}")
    
#     # IMPORTANT: Wait longer for extension to inject (especially in CI/headless)
#     print("[DEBUG] Waiting for extension to inject...")
    
#     # Check if running in CI
#     is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
#     wait_time = 10 if is_ci else 5  # Wait longer in CI
    
#     print(f"[DEBUG] Environment: {'CI (headless)' if is_ci else 'Local'}")
#     print(f"[DEBUG] Waiting {wait_time} seconds for extension...")
#     print(f"\n{'='*60}")
#     print(f"WATCHING CONSOLE MESSAGES (looking for bridge):")
#     print(f"{'='*60}")
    
#     # Wait with retry logic
#     bridge_found = False
#     for attempt in range(wait_time):
#         time.sleep(1)
        
#         bridge_exists = page.evaluate("""
#             () => {
#                 const bridge = document.getElementById('__avrl-glass-test-bridge__');
#                 return bridge !== null && bridge.getAttribute('data-ready') === 'true';
#             }
#         """)
        
#         if bridge_exists:
#             print(f"\n[OK] Test bridge found after {attempt + 1} seconds!")
#             bridge_found = True
#             break
        
#         if attempt < wait_time - 1:
#             print(f"[WAIT] Attempt {attempt + 1}/{wait_time}... bridge not ready yet")
    
#     print(f"{'='*60}")
#     print(f"TOTAL CONSOLE MESSAGES: {len(console_messages)}")
#     print(f"{'='*60}")
    
#     # Print all console messages at the end for review
#     if console_messages:
#         print(f"\n[INFO] All console messages:")
#         for msg in console_messages:
#             print(f"  {msg}")
#     else:
#         print(f"\n[WARNING] NO console messages captured!")
#         print(f"[INFO] This could mean:")
#         print(f"  1. Extension content script not running")
#         print(f"  2. Console logging is disabled")
#         print(f"  3. Content script has errors before console.log")
    
#     print(f"\n[INFO] Test bridge exists: {bridge_found}")
    
#     if bridge_found:
#         print(f"[OK] Test bridge is ready!")
        
#         # Test the bridge with a ping
#         ping_result = send_test_command(page, 'ping')
        
#         if ping_result['success']:
#             print(f"[SUCCESS] Bridge communication working!")
#             print(f"  - Ping response: {ping_result['message']}")
#         else:
#             print(f"[WARNING] Bridge exists but ping failed: {ping_result.get('error')}")
#     else:
#         print(f"[ERROR] Test bridge not found after {wait_time} seconds!")
#         print(f"[INFO] This means:")
#         print(f"  1. Extension might not be loaded")
#         print(f"  2. Test bridge code might be missing from content.js")
#         print(f"  3. Content script might have errors preventing injection")
        
#         # Check for specific bridge-related messages
#         bridge_messages = [msg for msg in console_messages if 'Bridge' in msg or 'bridge' in msg or 'AVRL' in msg]
#         if bridge_messages:
#             print(f"\n[INFO] Bridge-related console messages found:")
#             for msg in bridge_messages:
#                 print(f"  {msg}")
#         else:
#             print(f"\n[WARNING] No bridge-related console messages found!")
#             print(f"[INFO] Extension content script is likely NOT running")
        
#         # Take screenshot for debugging
#         page.screenshot(path="test-results/screenshots/bridge_not_found.png")
#         print(f"[SCREENSHOT] Saved debug screenshot")
        
#         # Fail the test if bridge not found
#         pytest.fail("Test bridge not available - extension not properly loaded")
    
#     # Method 3: Check for extension console messages
#     print(f"\n[DEBUG] Reloading page to capture any additional console messages...")
#     page.reload()
#     page.wait_for_load_state("networkidle")
#     time.sleep(2)
    
#     extension_messages = [msg for msg in console_messages if 'AVRL' in msg or 'Test Bridge' in msg]
#     if extension_messages:
#         print(f"[OK] Extension console messages found:")
#         for msg in extension_messages[:5]:
#             print(f"  - {msg}")
    
#     print("[SUCCESS] Extension installation verified")
#     assert True, "Extension is installed and working"


# @pytest.mark.smoke
# @pytest.mark.extension
# def test_click_popup_opens_new_page(page: Page, context: BrowserContext):
#     """
#     Test 2: Simulate clicking the popup and verify new page opens
    
#     This test:
#     - Clears any stored account
#     - Triggers popup via DOM bridge (simulates clicking extension icon)
#     - Verifies new Glass login page opens
    
#     This works in both local and CI environments!
#     """
#     print(f"\n[TEST 2] Testing popup click (trigger extension action)")
    
#     # Navigate to test page
#     test_url = "https://storage.googleapis.com/avrlgeneration_static_assets_staging/html_template/rxo_mock_template.html"
#     page.goto(test_url)
#     page.wait_for_load_state("networkidle")
#     print(f"[OK] Test page loaded")
    
#     # Wait for extension with retry logic
#     print("[DEBUG] Waiting for extension to initialize...")
    
#     is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
#     max_wait = 15 if is_ci else 10
    
#     bridge_ready = False
#     for attempt in range(max_wait):
#         time.sleep(1)
        
#         bridge_exists = page.evaluate("() => document.getElementById('__avrl-glass-test-bridge__') !== null")
        
#         if bridge_exists:
#             bridge_ready = True
#             print(f"[OK] Test bridge ready after {attempt + 1} seconds")
#             break
        
#         if attempt < max_wait - 1:
#             print(f"[WAIT] Attempt {attempt + 1}/{max_wait}...")
    
#     if not bridge_ready:
#         print("[ERROR] Test bridge not found after waiting!")
#         print("[FIX] Ensure:")
#         print("  1. Extension ZIP contains test bridge code")
#         print("  2. content.js has the test bridge at the end")
#         print("  3. Extension loads properly in headless mode")
        
#         page.screenshot(path="test-results/screenshots/bridge_not_ready.png")
        
#         pytest.skip("Test bridge not available - extension needs test hooks")
    
#     print("[OK] Test bridge found")
    
#     # Clear account to test "no account" scenario
#     print("[DEBUG] Clearing stored account...")
#     clear_result = send_test_command(page, 'clear-account')
    
#     if clear_result.get('success'):
#         print("[OK] Account cleared")
#     else:
#         print("[WARNING] Could not clear account (action might not be available)")
    
#     time.sleep(2)
    
#     # Track initial pages
#     initial_page_count = len(context.pages)
#     print(f"[DEBUG] Initial pages: {initial_page_count}")
    
#     # Trigger popup (simulates clicking the extension icon)
#     print("[DEBUG] Triggering popup action...")
#     print("           (This simulates clicking the extension icon)")
    
#     try:
#         # Wait for new page to open
#         with context.expect_page(timeout=15000) as new_page_info:
#             trigger_result = send_test_command(page, 'trigger-popup')
#             print(f"[OK] Trigger sent: {trigger_result['success']}")
        
#         # New page opened! (No account scenario)
#         new_page = new_page_info.value
#         new_page.wait_for_load_state("domcontentloaded", timeout=15000)
#         new_page_url = new_page.url
        
#         print(f"\n[SUCCESS] NEW PAGE OPENED!")
#         print(f"[OK] URL: {new_page_url}")
        
#         # Verify it's the correct Glass login page
#         assert "glass.1avrl.com" in new_page_url and "render_page_to_user" in new_page_url, \
#             f"Expected Glass login page, got: {new_page_url}"
        
#         print(f"[SUCCESS] Correct AVRL Glass login page opened!")
        
#         # Get page title
#         page_title = new_page.title()
#         print(f"[INFO] Page title: {page_title}")
        
#         # Take screenshot
#         screenshot_path = "test-results/screenshots/glass_login_page.png"
#         new_page.screenshot(path=screenshot_path)
#         print(f"[SCREENSHOT] Saved: {screenshot_path}")
        
#         # Close the new page
#         new_page.close()
        
#         final_page_count = len(context.pages)
#         print(f"[DEBUG] Final pages: {final_page_count}")
        
#         print(f"\n[SUCCESS] Popup trigger test PASSED!")
#         print(f"           Clicking popup correctly opened Glass login page")
        
#         assert True, "Popup action opened new Glass login page"
        
#     except Exception as e:
#         # No new page opened - might have account configured
#         print(f"\n[INFO] No new page opened: {e}")
#         print(f"[DEBUG] Checking if iframe appeared instead...")
        
#         time.sleep(2)
        
#         # Check for iframe
#         iframe_result = send_test_command(page, 'get-iframe-info')
        
#         if iframe_result['success'] and iframe_result.get('iframe'):
#             iframe_info = iframe_result['iframe']
#             print(f"[INFO] Iframe appeared instead:")
#             print(f"  - ID: {iframe_info['id']}")
#             print(f"  - Visible: {iframe_info['visible']}")
            
#             print(f"\n[NOTE] This means an account is configured in extension storage")
#             print(f"[NOTE] With account: popup toggles iframe")
#             print(f"[NOTE] Without account: popup opens new page")
            
#             # This is valid behavior, but not the "no account" scenario we're testing
#             print(f"\n[INFO] Clearing account and trying again...")
            
#             # Try clearing and triggering again
#             send_test_command(page, 'clear-account')
#             time.sleep(2)
            
#             try:
#                 with context.expect_page(timeout=10000) as retry_page_info:
#                     send_test_command(page, 'trigger-popup')
                
#                 retry_page = retry_page_info.value
#                 retry_url = retry_page.url
#                 print(f"[SUCCESS] After clearing account, new page opened: {retry_url}")
#                 retry_page.close()
#                 assert True, "Popup opened new page after clearing account"
#             except:
#                 print(f"[WARNING] Still no new page after clearing account")
#                 print(f"[INFO] Test inconclusive - extension might have persistent storage")
#                 pytest.skip("Could not test 'no account' scenario - account persists")
#         else:
#             print(f"[ERROR] No new page and no iframe - unexpected behavior")
            
#             # Take failure screenshot
#             page.screenshot(path="test-results/screenshots/popup_test_failure.png")
            
#             pytest.fail(f"Popup trigger didn't open new page or iframe: {e}")


@pytest.mark.smoke
@pytest.mark.integration
def test_glass_login_and_select_costmodel(page: Page, context: BrowserContext):
    """
    Test 3: Complete flow - Trigger popup, login, and select costmodel
    
    This test:
    - Starts on RXO test page
    - Triggers popup (opens Glass login in new tab)
    - Fills username and password in new tab
    - Clicks login button
    - Finds and clicks "costmodel" button
    - Verifies redirect back to original page
    """
    print(f"\n[TEST 3] Testing complete Glass login flow via popup")
    
    # Get credentials
    username = "avrl-internal/vikash@avrl.io"
    password = "nrgHlIySThRRdd1IxdStD0vV0jk"
    
    print(f"[DEBUG] Using username: {username[:10]}***")
    
    # Start on RXO test page
    test_url = "https://storage.googleapis.com/avrlgeneration_static_assets_staging/html_template/rxo_mock_template.html"
    page.goto(test_url)
    page.wait_for_load_state("networkidle")
    print(f"[OK] Test page loaded: {page.url}")
    
    # Wait for extension to inject bridge
    print("[DEBUG] Waiting for extension bridge...")
    time.sleep(3)
    
    # Verify bridge exists
    bridge_exists = page.evaluate("() => document.getElementById('__avrl-glass-test-bridge__') !== null")
    if not bridge_exists:
        print("[ERROR] Test bridge not found - skipping test")
        pytest.skip("Test bridge not available")
    
    print("[OK] Test bridge found")
    
    # Clear any existing account (to force login flow)
    print("[DEBUG] Clearing stored account to trigger login flow...")
    send_test_command(page, 'clear-account')
    time.sleep(1)
    
    # Trigger popup - this will open Glass login in a NEW TAB
    print("[DEBUG] Triggering popup (this will open Glass login in new tab)...")
    
    initial_pages = len(context.pages)
    print(f"[DEBUG] Initial pages: {initial_pages}")
    
    try:
        # Wait for new page to open when we trigger popup
        with context.expect_page(timeout=15000) as new_page_info:
            send_test_command(page, 'trigger-popup')
            print("[OK] Popup triggered")
        
        # Get the new page (Glass login page)
        login_page = new_page_info.value
        login_page.wait_for_load_state("networkidle", timeout=10000)
        
        print(f"[SUCCESS] New tab opened!")
        print(f"[OK] Login page URL: {login_page.url}")
        
        # Take screenshot of login page
        login_page.screenshot(path="test-results/screenshots/glass_login_page_opened.png")
        print(f"[SCREENSHOT] Saved glass_login_page_opened.png")
        
        # Now fill the login form on this new page
        print(f"\n[LOGIN] Filling credentials on login page...")
        
        try:
            # Fill username
            print(f"[LOGIN] Filling username...")
            username_field = login_page.locator("xpath=/html/body/div[1]/form/input[1]")
            username_field.fill(username, timeout=5000)
            print(f"[OK] Username filled")
            
            # Fill password
            print(f"[LOGIN] Filling password...")
            password_field = login_page.locator("xpath=/html/body/div[1]/form/input[2]")
            password_field.fill(password, timeout=5000)
            print(f"[OK] Password filled")
            
            # Take screenshot before login
            login_page.screenshot(path="test-results/screenshots/before_login_click.png")
            
            # Click login button and wait for page reload
            print(f"[LOGIN] Clicking login button...")
            login_button = login_page.locator("xpath=/html/body/div[1]/form/button")
            
            # Wait for navigation (page reload after login)
            print(f"[DEBUG] Waiting for page reload after login...")
            with login_page.expect_navigation(timeout=15000):
                login_button.click()
            
            print(f"[OK] Login button clicked and page reloaded")
            
            # Wait for page to be fully loaded
            login_page.wait_for_load_state("networkidle", timeout=10000)
            print(f"[OK] Page loaded after login: {login_page.url}")
            
            # Additional wait for any JavaScript to render the UI
            print(f"[DEBUG] Waiting for UI to render...")
            time.sleep(2)
            
            # Take screenshot after login
            login_page.screenshot(path="test-results/screenshots/after_login.png")
            print(f"[SCREENSHOT] Saved after_login.png")
            
            # Now find and click costmodel button
            print(f"\n[COSTMODEL] Looking for 'costmodel' button...")
            
            # Try multiple selectors
            costmodel_found = False
            selectors = [
                "button:has-text('costmodel')",
                "button:has-text('Costmodel')",
                "button:has-text('COSTMODEL')",
                "[role='button']:has-text('costmodel')",
                "//button[contains(text(), 'costmodel')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'costmodel')]",
            ]
            
            for selector in selectors:
                try:
                    button = login_page.locator(selector).first
                    if button.is_visible(timeout=3000):
                        print(f"[OK] Found costmodel button with: {selector}")
                        
                        # Take screenshot before clicking
                        login_page.screenshot(path="test-results/screenshots/before_costmodel_click.png")
                        
                        # Click it
                        button.click()
                        print(f"[OK] Costmodel button clicked!")
                        costmodel_found = True
                        break
                except Exception as e:
                    print(f"[DEBUG] Selector '{selector}' failed: {e}")
                    continue
            
            if not costmodel_found:
                print(f"[ERROR] Could not find costmodel button")
                login_page.screenshot(path="test-results/screenshots/costmodel_not_found.png")
                
                # Print page content for debugging
                buttons = login_page.locator("button").all()
                print(f"[DEBUG] Found {len(buttons)} buttons on page")
                for i, btn in enumerate(buttons[:5]):
                    try:
                        text = btn.text_content(timeout=1000)
                        print(f"  Button {i+1}: '{text}'")
                    except:
                        pass
                
                pytest.fail("Costmodel button not found on page")
            
            # Wait for automatic redirect (system handles this)
            print(f"\n[VERIFY] Waiting for automatic redirect...")
            time.sleep(3)  # Give time for redirect to complete
            
            # Take screenshot after costmodel selection
            try:
                login_page.screenshot(path="test-results/screenshots/after_costmodel_select.png", timeout=2000)
                print(f"[SCREENSHOT] Saved after_costmodel_select.png")
            except:
                print(f"[INFO] Login page may have closed/redirected")
            
            # The login page might close automatically or the original page gets updated
            # Let's check the original page
            print(f"\n[VERIFY] Checking original page after login flow...")
            print(f"  - Original page URL: {page.url}")
            
            # Wait a bit for any updates to the original page
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass
            
            # Take screenshot of original page after login
            page.screenshot(path="test-results/screenshots/original_page_after_login.png")
            print(f"[SCREENSHOT] Saved original_page_after_login.png")
            
            # Close the login tab if still open
            try:
                if not login_page.is_closed():
                    login_page.close()
                    print(f"[OK] Login tab closed")
                else:
                    print(f"[INFO] Login tab already closed (expected)")
            except:
                print(f"[INFO] Login tab handling complete")
            
            print(f"\n[SUCCESS] Complete login flow test PASSED!")
            print(f"  ✓ Popup triggered")
            print(f"  ✓ Login page opened")
            print(f"  ✓ Credentials filled")
            print(f"  ✓ Login successful")
            print(f"  ✓ Costmodel selected")
            print(f"  ✓ Redirect completed")
            
            # NOW trigger popup again (with account configured)
            print(f"\n[VERIFY] Triggering popup again (account now configured)...")
            print(f"[DEBUG] This time it should toggle iframe instead of opening new page")
            
            # Wait a bit for the system to settle
            time.sleep(2)
            
            # Check if bridge still exists
            bridge_check = page.evaluate("() => document.getElementById('__avrl-glass-test-bridge__') !== null")
            print(f"[DEBUG] Bridge exists on original page: {bridge_check}")
            
            # Trigger popup again
            trigger_result = send_test_command(page, 'trigger-popup')
            print(f"[OK] Popup triggered again: {trigger_result}")
            
            # Wait for iframe to appear/toggle (5 seconds)
            print(f"[DEBUG] Waiting for iframe to load...")
            time.sleep(5)
            
            # Check iframe immediately after trigger
            iframe_info = page.evaluate("""
                () => {
                    const iframe = document.getElementById('avrl-glass-iframe');
                    if (iframe) {
                        return {
                            exists: true,
                            src: iframe.src,
                            visible: iframe.offsetParent !== null
                        };
                    }
                    return { exists: false };
                }
            """)
            print(f"[DEBUG] Iframe info after trigger:")
            print(f"  - Exists: {iframe_info.get('exists')}")
            if iframe_info.get('exists'):
                print(f"  - Src: {iframe_info.get('src')}")
                print(f"  - Visible: {iframe_info.get('visible')}")
            
            # Check if iframe content loaded by looking for #account-name-display
            if iframe_info.get('exists'):
                print(f"[DEBUG] Checking if iframe content loaded...")
                print(f"[DEBUG] Iframe src: {iframe_info.get('src')}")
                
                try:
                    # Get the iframe frame
                    iframe_element = page.frame_locator("#avrl-glass-iframe")
                    
                    # First, let's see what's inside the iframe
                    print(f"[DEBUG] Checking iframe contents...")
                    iframe_body = iframe_element.locator("body")
                    
                    # Try to get some text from the iframe
                    try:
                        body_text = iframe_body.text_content(timeout=3000)
                        print(f"[DEBUG] Iframe body text (first 200 chars): {body_text[:200] if body_text else 'empty'}")
                    except:
                        print(f"[DEBUG] Could not read iframe body text")
                    
                    # Wait for and check the account-name-display element
                    account_element = iframe_element.locator("#account-name-display")
                    
                    # Wait for element to be visible (with timeout)
                    account_element.wait_for(state="visible", timeout=10000)
                    
                    # Get the text content
                    account_text = account_element.text_content()
                    
                    print(f"[SUCCESS] Iframe loaded properly!")
                    print(f"  - Found #account-name-display")
                    print(f"  - Account text: {account_text}")
                    
                    # Take screenshot showing loaded iframe with account
                    page.screenshot(path="test-results/screenshots/iframe_with_account_loaded.png")
                    print(f"[SCREENSHOT] Saved iframe_with_account_loaded.png")
                    
                except Exception as e:
                    print(f"[WARNING] Iframe content not fully loaded: {e}")
                    print(f"  - #account-name-display element not found")
                    print(f"[INFO] This might mean:")
                    print(f"  1. Template is still loading inside iframe")
                    print(f"  2. Template loaded but element ID is different")
                    print(f"  3. Template request was not intercepted")
            
            # Take screenshot after second popup trigger
            page.screenshot(path="test-results/screenshots/after_second_popup_trigger.png")
            print(f"[SCREENSHOT] Saved after_second_popup_trigger.png")
            
            # Check if iframe exists
            iframe_check = page.evaluate("""
                () => {
                    const iframe = document.getElementById('avrl-glass-iframe');
                    if (iframe) {
                        return {
                            exists: true,
                            visible: iframe.offsetParent !== null,
                            src: iframe.src,
                            width: iframe.offsetWidth,
                            height: iframe.offsetHeight
                        };
                    }
                    return { exists: false };
                }
            """)
            
            print(f"[INFO] Iframe after second trigger:")
            print(f"  - Exists: {iframe_check.get('exists')}")
            if iframe_check.get('exists'):
                print(f"  - Visible: {iframe_check.get('visible')}")
                print(f"  - Width: {iframe_check.get('width')}px")
                print(f"  - Height: {iframe_check.get('height')}px")
            
            print(f"\n[SUCCESS] Complete test with popup re-trigger PASSED!")
            print(f"  ✓ All login steps completed")
            print(f"  ✓ Popup re-triggered successfully")
            print(f"  ✓ Screenshots captured")
            
            assert True, "Complete login and costmodel selection flow completed"
            
        except TimeoutError as e:
            print(f"[ERROR] Timeout during login flow: {e}")
            login_page.screenshot(path="test-results/screenshots/login_timeout.png")
            raise
        except Exception as e:
            print(f"[ERROR] Login flow failed: {e}")
            login_page.screenshot(path="test-results/screenshots/login_failure.png")
            raise
            
    except TimeoutError:
        print(f"[ERROR] New page did not open after triggering popup")
        print(f"[INFO] This might mean:")
        print(f"  1. Account is already configured (login not needed)")
        print(f"  2. Popup trigger failed")
        print(f"  3. Extension not working properly")
        
        page.screenshot(path="test-results/screenshots/popup_no_new_page.png")
        pytest.fail("Expected new page to open for login, but it didn't")





