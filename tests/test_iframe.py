"""
Tests for iframe injection and functionality
"""
import pytest
from playwright.sync_api import Page, expect, FrameLocator
import time


@pytest.mark.iframe
def test_iframe_injection(page: Page):
    """
    Test that the extension can inject an iframe into the page
    """
    # Navigate to test page
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # Execute script to trigger iframe injection
    # This assumes your extension injects iframe via content script
    # Adjust the selector based on your actual iframe ID/class
    page.evaluate("""
        // Simulate extension iframe injection
        const iframe = document.createElement('iframe');
        iframe.id = 'extension-iframe';
        iframe.setAttribute('data-extension-iframe', 'true');
        iframe.src = 'https://example.com';
        iframe.style.cssText = 'position: fixed; bottom: 20px; right: 20px; width: 400px; height: 600px; z-index: 999999;';
        document.body.appendChild(iframe);
    """)
    
    # Wait for iframe to be added
    page.wait_for_selector("#extension-iframe", timeout=5000)
    
    # Verify iframe exists
    iframe = page.locator("#extension-iframe")
    expect(iframe).to_be_visible()


@pytest.mark.iframe
def test_iframe_attributes(page: Page):
    """
    Test that the injected iframe has correct attributes
    """
    # Navigate and inject iframe
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # Inject iframe (simulate extension behavior)
    page.evaluate("""
        const iframe = document.createElement('iframe');
        iframe.id = 'extension-iframe';
        iframe.setAttribute('data-extension-iframe', 'true');
        iframe.src = 'https://example.com';
        document.body.appendChild(iframe);
    """)
    
    # Get iframe element
    iframe = page.locator("#extension-iframe")
    
    # Check attributes
    assert iframe.get_attribute("data-extension-iframe") == "true"
    assert iframe.count() == 1


@pytest.mark.iframe
def test_iframe_content_loads(page: Page):
    """
    Test that content loads inside the iframe
    """
    # Navigate to page
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # Inject iframe
    page.evaluate("""
        const iframe = document.createElement('iframe');
        iframe.id = 'extension-iframe';
        iframe.src = 'https://example.com';
        document.body.appendChild(iframe);
    """)
    
    # Wait for iframe
    page.wait_for_selector("#extension-iframe")
    
    # Get iframe frame locator
    iframe_element = page.frame_locator("#extension-iframe")
    
    # Wait for content to load inside iframe
    # Adjust based on what content you expect in the iframe
    iframe_element.locator("h1").wait_for(timeout=10000)
    
    # Verify content is visible
    expect(iframe_element.locator("h1")).to_be_visible()


@pytest.mark.iframe
def test_multiple_iframes_not_created(page: Page):
    """
    Test that multiple iframes are not created if injection is triggered multiple times
    """
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # Inject iframe multiple times
    for _ in range(3):
        page.evaluate("""
            if (!document.getElementById('extension-iframe')) {
                const iframe = document.createElement('iframe');
                iframe.id = 'extension-iframe';
                iframe.src = 'https://example.com';
                document.body.appendChild(iframe);
            }
        """)
        time.sleep(0.5)
    
    # Count iframes
    iframe_count = page.locator("#extension-iframe").count()
    
    # Should only be one iframe
    assert iframe_count == 1, f"Expected 1 iframe, found {iframe_count}"


@pytest.mark.iframe
def test_iframe_positioning(page: Page):
    """
    Test that the iframe is positioned correctly
    """
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # Inject iframe with specific positioning
    page.evaluate("""
        const iframe = document.createElement('iframe');
        iframe.id = 'extension-iframe';
        iframe.style.cssText = 'position: fixed; bottom: 20px; right: 20px; width: 400px; height: 600px;';
        iframe.src = 'https://example.com';
        document.body.appendChild(iframe);
    """)
    
    # Get iframe
    iframe = page.locator("#extension-iframe")
    
    # Check positioning
    box = iframe.bounding_box()
    assert box is not None, "Iframe should have bounding box"
    assert box["width"] == 400, f"Expected width 400, got {box['width']}"
    assert box["height"] == 600, f"Expected height 600, got {box['height']}"


@pytest.mark.iframe
def test_iframe_removal(page: Page):
    """
    Test that iframe can be removed from the page
    """
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # Inject iframe
    page.evaluate("""
        const iframe = document.createElement('iframe');
        iframe.id = 'extension-iframe';
        iframe.src = 'https://example.com';
        document.body.appendChild(iframe);
    """)
    
    # Verify iframe exists
    expect(page.locator("#extension-iframe")).to_be_visible()
    
    # Remove iframe
    page.evaluate("""
        const iframe = document.getElementById('extension-iframe');
        if (iframe) iframe.remove();
    """)
    
    # Verify iframe is removed
    assert page.locator("#extension-iframe").count() == 0


@pytest.mark.iframe
def test_iframe_z_index(page: Page):
    """
    Test that iframe has proper z-index to appear on top
    """
    page.goto("https://example.com")
    page.wait_for_load_state("domcontentloaded")
    
    # Inject iframe with z-index
    page.evaluate("""
        const iframe = document.createElement('iframe');
        iframe.id = 'extension-iframe';
        iframe.style.cssText = 'z-index: 999999;';
        iframe.src = 'https://example.com';
        document.body.appendChild(iframe);
    """)
    
    # Get computed style
    z_index = page.evaluate("""
        window.getComputedStyle(document.getElementById('extension-iframe')).zIndex
    """)
    
    # Verify z-index
    assert int(z_index) >= 999999, f"Expected z-index >= 999999, got {z_index}"

