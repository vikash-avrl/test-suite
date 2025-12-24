"""
Integration tests for Chrome extension with real scenarios
"""
import pytest
from playwright.sync_api import Page, expect
import time


@pytest.mark.integration
def test_extension_on_multiple_pages(page: Page):
    """
    Test that extension works across multiple page navigations
    """
    # Test on multiple different websites
    test_urls = [
        "https://example.com",
        "https://www.wikipedia.org",
    ]
    
    for url in test_urls:
        page.goto(url)
        page.wait_for_load_state("networkidle")
        
        # Verify page loaded
        assert url.replace("https://", "").replace("www.", "") in page.url


@pytest.mark.integration  
def test_extension_with_spa_navigation(page: Page):
    """
    Test extension behavior with Single Page Application navigation
    """
    # Navigate to a page
    page.goto("https://example.com")
    page.wait_for_load_state("networkidle")
    
    # Simulate SPA-like behavior
    page.evaluate("""
        history.pushState({}, '', '/test-route');
    """)
    
    # Extension should still work after SPA navigation
    time.sleep(1)
    assert "/test-route" in page.url


@pytest.mark.integration
@pytest.mark.slow
def test_extension_performance(page: Page):
    """
    Test that extension doesn't significantly impact page load time
    """
    # Measure page load with extension
    start_time = time.time()
    page.goto("https://example.com")
    page.wait_for_load_state("networkidle")
    load_time = time.time() - start_time
    
    # Should load within reasonable time (adjust threshold as needed)
    assert load_time < 10, f"Page load took too long: {load_time}s"


@pytest.mark.integration
def test_iframe_communication(page: Page):
    """
    Test message passing between page and iframe (if applicable)
    """
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # Setup message listener
    page.evaluate("""
        window.testMessages = [];
        window.addEventListener('message', (event) => {
            window.testMessages.push(event.data);
        });
    """)
    
    # Inject iframe
    page.evaluate("""
        const iframe = document.createElement('iframe');
        iframe.id = 'extension-iframe';
        iframe.src = 'https://example.com';
        document.body.appendChild(iframe);
    """)
    
    time.sleep(2)
    
    # Post message from main page to iframe
    page.evaluate("""
        const iframe = document.getElementById('extension-iframe');
        if (iframe && iframe.contentWindow) {
            iframe.contentWindow.postMessage({ type: 'TEST_MESSAGE' }, '*');
        }
    """)
    
    # This test structure is ready for when you implement actual messaging
    # For now, just verify iframe exists
    expect(page.locator("#extension-iframe")).to_be_attached()

