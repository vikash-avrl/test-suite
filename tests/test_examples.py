"""
Example of how to adapt tests to your specific extension

This file shows how to customize the base tests to work with YOUR Chrome extension.
Copy patterns from here into your actual test files.
"""
import pytest
from playwright.sync_api import Page, expect


# Example: If your extension injects iframe on button click
@pytest.mark.iframe
def test_extension_button_triggers_iframe(page: Page):
    """
    Test that clicking extension button injects iframe
    """
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # If your extension has a popup with a button
    # You would click it like this:
    # page.locator("button[data-extension-trigger]").click()
    
    # Wait for iframe to appear
    # Replace '#extension-iframe' with YOUR iframe selector
    page.wait_for_selector("#extension-iframe", timeout=5000)
    
    # Verify
    expect(page.locator("#extension-iframe")).to_be_visible()


# Example: If your iframe loads specific content
@pytest.mark.iframe
def test_iframe_loads_your_template(page: Page):
    """
    Test that the iframe loads your specific template/webpage
    """
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # Wait for iframe (adjust selector to match yours)
    page.wait_for_selector("#extension-iframe")
    
    # Access iframe content
    iframe = page.frame_locator("#extension-iframe")
    
    # Check for specific elements in YOUR template
    # Replace these with actual elements from your template
    expect(iframe.locator(".your-template-class")).to_be_visible()
    # expect(iframe.locator("h1")).to_contain_text("Your Expected Text")


# Example: Testing iframe with specific URL
@pytest.mark.iframe  
def test_iframe_source_url(page: Page):
    """
    Test that iframe loads from correct URL
    """
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # Get iframe element
    iframe = page.locator("#extension-iframe")
    
    # Check the src attribute
    iframe_src = iframe.get_attribute("src")
    
    # Replace with YOUR expected iframe URL
    assert "your-template-url.com" in iframe_src


# Example: Testing multiple pages
@pytest.mark.integration
def test_extension_works_on_different_sites(page: Page):
    """
    Test that extension works across different websites
    """
    test_sites = [
        "https://github.com",
        "https://stackoverflow.com",
        "https://example.com",
    ]
    
    for site in test_sites:
        page.goto(site)
        page.wait_for_load_state("networkidle")
        
        # Verify your extension iframe appears
        # Adjust timeout and selector as needed
        try:
            page.wait_for_selector("#extension-iframe", timeout=3000)
            assert page.locator("#extension-iframe").count() == 1
        except Exception as e:
            pytest.fail(f"Extension failed on {site}: {str(e)}")


# Example: Testing extension communication
@pytest.mark.integration
def test_extension_message_passing(page: Page):
    """
    Test communication between page and extension iframe
    """
    page.goto("https://example.com")
    
    # Setup listener for messages
    page.evaluate("""
        window.receivedMessages = [];
        window.addEventListener('message', (event) => {
            window.receivedMessages.push(event.data);
        });
    """)
    
    # Wait for iframe
    page.wait_for_selector("#extension-iframe")
    
    # Send message to iframe
    page.evaluate("""
        const iframe = document.getElementById('extension-iframe');
        iframe.contentWindow.postMessage({ type: 'PING' }, '*');
    """)
    
    # Wait a bit for response
    page.wait_for_timeout(1000)
    
    # Check if messages were received
    messages = page.evaluate("window.receivedMessages")
    
    # Add your specific message validation here
    # assert len(messages) > 0


# Example: Testing with authentication/cookies
@pytest.mark.integration
def test_extension_with_authentication(page: Page):
    """
    Test extension behavior when user is authenticated
    """
    # Set authentication cookies if needed
    page.context.add_cookies([{
        "name": "session_token",
        "value": "test_token_12345",
        "domain": "example.com",
        "path": "/"
    }])
    
    page.goto("https://example.com")
    
    # Your extension might behave differently when authenticated
    # Add your specific tests here


# Example: Performance testing
@pytest.mark.slow
def test_extension_performance_impact(page: Page):
    """
    Test that extension doesn't slow down page load significantly
    """
    import time
    
    # Measure load time
    start = time.time()
    page.goto("https://example.com")
    page.wait_for_load_state("networkidle")
    load_time = time.time() - start
    
    # Adjust threshold based on your requirements
    assert load_time < 5.0, f"Page load took {load_time}s, expected < 5s"

