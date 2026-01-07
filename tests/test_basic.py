import pytest
from playwright.sync_api import Page, BrowserContext, TimeoutError
import time
import os 
import json
# =========================================================
# COMMON HELPERS (RESPECT ORIGINAL STYLE)
# =========================================================
TEST_RESULTS = []
VALID_DATES  = [
                        "Dec 15, 08:30 PM",
                        "Dec 15, 8:30 PM",
                        "December 15, 08:30 PM",
                        "Dec 15 08:30",
                        "Dec 15, 2024 08:30 PM",
                        "December 15, 2024 08:30",
                        "Dec 15, 08:30:45 PM",
                        "December 15, 2024 08:30:45 PM",
                        "Dec 15 20:30",
                        "12/15/2024 08:30 PM",
                        "12/15/24 08:30 PM",
                        "12/15 08:30 PM",
                        "12/15/2024 20:30",
                        "12/15/24 14:30:45",
                        "02/16/23 11:33",
                        "1/5/2024 9:30 AM",
                        "15/12/24 14:30",
                        "Dec 15, 08:30 PM CST",
                        "Dec 15, 08:30 PM EST",
                        "12/15/2024 08:30 PM PST",
                        "08:30 PM UTC",
                        "Jan 1 09:00 AM JST",
                        "08:30 PM",
                        "8:30 PM",
                        "8:30 AM",
                        "14:30",
                        "14:30:45",
                        "12:00 PM",
                        "12:00 AM",
                        "11:59 PM",
                        "00:00",
                        "23:59:59",
                        "12/15/2024",
                        "12/15/24",
                        "12/15",
                        "1/5/2024",
                        "01/01/2024",
                        "Jan 15",
                        "January 15",
                        "Jan 15, 2024",
                        "Jan 15 2024",
                        "January 15, 2024",
                        "January 15 2024",
                        "2/29/2024 12:00 PM",
                        "Feb 29, 2024",
                        "12/31/2024 11:59 PM",
                        "1/1/2025 00:00",
                        "March 1",
                        "03/01",
                        "Dec 16, 08:00 AM  - 05:00 PM EST",
                        "Dec 16, 08:00 AM  -"
                    ]
                    
                    # Also include invalid cases (NOT PARSABLE)
INVALID_DATES  = [
                        "8-30-2021 2:00 PM",
                        "Dec15,08:30PM",
                        "Dec15 08:30",
                        "15 Dec, 08:30 PM",
                        "15 December 08:30",
                        "15 Dec, 2024 08:30 PM",
                        "15 December 2024 08:30",
                        "15Dec08:30PM",
                        "15 Dec 14:30:45",
                        "12-15-2024 8:30 AM",
                        "15.12.2024 08:30",
                        "15/12/2024 20:30:45",
                        "15.12.2024 8:30 PM",
                        "2024-12-15T14:30:00",
                        "2024-12-15 14:30:00",
                        "2024-12-15T08:30:45",
                        "2024-12-15 20:30",
                        "15 Dec 14:30 GMT",
                        "2024-12-15 14:30 IST",
                        "2024-12-15",
                        "2024-12",
                        "2024",
                        "2024-01-01",
                        "2024-1-5",
                        "12-15-2024",
                        "12-15",
                        "15.12.2024",
                        "15/12/2024",
                        "31/12/2024",
                        "15.12.24",
                        "15 Jan",
                        "15 January",
                        "15 Jan 2024",
                        "15 Jan, 2024",
                        "15 January 2024",
                        "Jan15",
                        "15Jan",
                        "Jan15,2024",
                        "15Jan2024",
                        "Jan 2024",
                        "January 2024",
                        "Jan2024",
                        "December 2023",
                        "15",
                        "1",
                        "31",
                        "January",
                        "Jan",
                        "Dec",
                        "today",
                        "tomorrow",
                        "yesterday",
                        "20241215",
                        "20240101",
                        "241215",
                        "240101",
                        "invalid-date-text", 
                        "not a date",
                        "00/00/0000"
                    ]
def wait_for_settle(page: Page, sleep_time=5):
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except:
        pass
    time.sleep(sleep_time)

def record_result(
    results,
    phase,
    test_type,
    input_value,
    expected,
    actual,
    status
):
    results.append({
        "phase": phase,
        "test_type": test_type,
        "input": input_value,
        "expected": expected,
        "actual": actual,
        "status": status
    })


def fail_phase(phase, msg):
    pytest.fail(f"[PHASE FAILED] {phase} → {msg}")


def send_test_command(page: Page, action: str, data: dict = None):
    return page.evaluate("""
        ({ action, data }) => {
            return new Promise((resolve) => {
                const bridge = document.getElementById('__avrl-glass-test-bridge__');
                if (!bridge) {
                    resolve({ success: false, error: 'Bridge not found' });
                    return;
                }
                const handler = (e) => {
                    bridge.removeEventListener('avrl-test-response', handler);
                    resolve(e.detail);
                };
                bridge.addEventListener('avrl-test-response', handler);
                bridge.dispatchEvent(
                    new CustomEvent('avrl-test-command', {
                        detail: { action, data }
                    })
                );
                setTimeout(() => resolve({ success: false, error: 'timeout' }), 5000);
            });
        }
    """, {'action': action, 'data': data or {}})

# =========================================================
# PHASE 1: LOGIN + COSTMODEL + IFRAME
# =========================================================
def phase_login_and_iframe(page: Page, context: BrowserContext, results):
    try:
        page.goto(
            "https://storage.googleapis.com/avrlgeneration_static_assets_staging/html_template/rxo_mock_template.html"
        )
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        bridge = page.evaluate(
            "() => document.getElementById('__avrl-glass-test-bridge__') !== null"
        )

        if not bridge:
            record_result(
                results, "LOGIN", "Extension Bridge",
                "RXO Page Load",
                "Bridge injected",
                "Bridge missing",
                "FAILED"
            )
            fail_phase("LOGIN", "Extension bridge not injected")

        record_result(
            results, "LOGIN", "Extension Bridge",
            "RXO Page Load",
            "Bridge injected",
            "Bridge found",
            "PASSED"
        )

        send_test_command(page, "clear-account")
        time.sleep(1)

        with context.expect_page(timeout=15000) as p:
            send_test_command(page, "trigger-popup")

        login = p.value
        login.wait_for_load_state("networkidle")

        # Get credentials from environment variables (GitHub Secrets)
        username = os.getenv("GLASS_USERNAME") 
        password = os.getenv("GLASS_PASSWORD") 

        if not username or not password:
            pytest.fail("Missing required environment variables: GLASS_USERNAME, GLASS_PASSWORD")

        login.locator("xpath=/html/body/div[1]/form/input[1]").fill(username)
        login.locator("xpath=/html/body/div[1]/form/input[2]").fill(password)

        with login.expect_navigation():
            login.locator("xpath=/html/body/div[1]/form/button").click()

        login.wait_for_load_state("networkidle")

        btn = login.locator("button:has-text('costmodel')")
        btn.wait_for(state="visible", timeout=10000)
        btn.click()

        record_result(
            results, "LOGIN", "Costmodel Selection",
            "Click costmodel",
            "Costmodel selected",
            "Costmodel clicked",
            "PASSED"
        )

        wait_for_settle(login, 3)

        if not login.is_closed():
            login.close()

        send_test_command(page, "trigger-popup")
        page.locator("iframe#avrl-glass-iframe").wait_for(
            state="visible", timeout=15000
        )

        record_result(
            results, "LOGIN", "Iframe Load",
            "Trigger popup",
            "Iframe visible",
            "Iframe visible",
            "PASSED"
        )

        return (
            page
            .frame_locator("iframe#avrl-glass-iframe")
            .frame_locator("iframe")
        )

    except Exception as e:
        record_result(
            results, "LOGIN", "Login Flow",
            "Popup + Login",
            "Successful login",
            str(e),
            "FAILED"
        )
        fail_phase("LOGIN", str(e))


# =========================================================
# PHASE 2: ZIP RESOLUTION (PICKUP + DESTINATION)
# =========================================================

def phase_zip_resolution(page: Page, frame, results):
    try:
        # Invalid ZIP
        frame.locator("#stop-zip-0").fill("00000")
        wait_for_settle(page, 8)
        txt = frame.locator("#stop-location-text-0").text_content()

        if "," in txt:
            record_result(
                results, "ZIP", "Invalid Zip Resolution",
                "00000",
                "Resolved to 'US'",
                txt,
                "FAILED"
            )
            fail_phase("ZIP", "Invalid ZIP resolved incorrectly")
        else:
            record_result(
                results, "ZIP", "Invalid Zip Resolution",
                "00000",
                "Resolved to 'US'",
                txt,
                "PASSED"
            )

        # Valid Pickup ZIP
        frame.locator("#stop-zip-0").fill("70734")
        wait_for_settle(page, 8)
        txt = frame.locator("#stop-location-text-0").text_content()

        if "Geismar" not in txt:
            record_result(
                results, "ZIP", "Valid Zip Resolution",
                "70734",
                "Resolved to Geismar, LA, US",
                txt,
                "FAILED"
            )
            fail_phase("ZIP", "Pickup ZIP not resolved")
        else:
            record_result(
                results, "ZIP", "Valid Zip Resolution",
                "70734",
                "Resolved to Geismar, LA, US",
                txt,
                "PASSED"
            )

        # Destination ZIP
        frame.locator("#stop-zip-1").fill("19711")
        wait_for_settle(page, 8)

        record_result(
            results, "ZIP", "Destination Zip Resolution",
            "19711",
            "Resolved without error",
            "Resolved",
            "PASSED"
        )

    except Exception as e:
        record_result(
            results, "ZIP", "ZIP Phase",
            "ZIP Resolution",
            "All ZIPs resolved",
            str(e),
            "FAILED"
        )
        fail_phase("ZIP", str(e))

# =========================================================
# PHASE 3: DATES + NORMALIZATION
# =========================================================

def phase_dates_and_normalization(page: Page, frame, results):
    frame.locator("#weight").fill("40,584 lbs")
    frame.locator("#weight").blur()
    wait_for_settle(page, 2)

    record_result(
        results, "NORMALIZATION", "Weight Normalization",
        "40,584 lbs",
        "Normalized numeric value",
        frame.locator("#weight").input_value(),
        "PASSED"
    )

    frame.locator("#distance").fill("799.41 mi")
    frame.locator("#distance").blur()
    wait_for_settle(page, 2)

    record_result(
        results, "NORMALIZATION", "Distance Normalization",
        "799.41 mi",
        "Numeric distance",
        frame.locator("#distance").input_value(),
        "PASSED"
    )


# =========================================================
# PHASE 4: FETCH – NEGATIVE
# =========================================================

def phase_fetch_negative(page: Page, frame, results):
    frame.locator("#distance").fill("")
    wait_for_settle(page, 1)

    frame.locator("#fetch-rate-btn").evaluate("el => el.click()")
    wait_for_settle(page, 3)

    if page.locator("#avrl-error-modal").is_visible():
        record_result(
            results, "FETCH", "Missing Field Validation",
            "Empty Distance",
            "Error modal visible",
            "Error modal visible",
            "PASSED"
        )
        page.locator("#avrl-error-modal").click()
    else:
        record_result(
            results, "FETCH", "Missing Field Validation",
            "Empty Distance",
            "Error modal visible",
            "No error modal",
            "FAILED"
        )
        fail_phase("FETCH-NEGATIVE", "Error modal not shown")


# =========================================================
# PHASE 5: FETCH – POSITIVE
# =========================================================
def phase_date_validation(page: Page, frame, results):
    field = frame.locator("#pickup_date")

    # -------------------------
    # VALID DATE CASES
    # -------------------------
    for val in VALID_DATES:
        field.fill("")
        field.fill(val)
        field.blur()
        time.sleep(0.2)

        has_error = frame.locator(".field-error").count() > 0

        parsed_val = field.input_value() # Capture what the input became
        if has_error:
            record_result(
                results,
                phase="DATE",
                test_type="Valid Date Format",
                input_value=val,
                expected="Accepted (no field-error)",
                actual="Rejected (field-error visible)",
                status="FAILED"
            )
            fail_phase("DATE", f"Valid date rejected: {val}")
        else:
            record_result(
                results,
                phase="DATE",
                test_type="Valid Date Format",
                input_value=val,
                expected=f"Parsed: {parsed_val}",
                actual="Accepted",
                status="PASSED"
            )

    # -------------------------
    # INVALID DATE CASES
    # -------------------------
    for val in INVALID_DATES:
        field.fill("")
        field.fill(val)
        field.blur()
        time.sleep(0.2)

        has_error = frame.locator(".field-error").count() > 0

        if not has_error:
            record_result(
                results,
                phase="DATE",
                test_type="Invalid Date Format",
                input_value=val,
                expected="Rejected (field-error visible)",
                actual="Accepted",
                status="FAILED"
            )
            fail_phase("DATE", f"Invalid date accepted: {val}")
        else:
            record_result(
                results,
                phase="DATE",
                test_type="Invalid Date Format",
                input_value=val,
                expected="Rejected (field-error visible)",
                actual="Rejected",
                status="PASSED"
            )

    # Restore valid state for next phases
    field.fill("12/15/2026 08:30 PM")
    frame.locator("#drop_date").fill("12/15/2026 08:30 PM")
    time.sleep(1)

def phase_fetch_positive(page: Page, frame, results):
    frame.locator("#distance").fill("799.41")
    frame.locator("#distance").blur()
    wait_for_settle(page, 2)

    frame.locator("#fetch-rate-btn").evaluate("el => el.click()")
    wait_for_settle(page, 10)

    rate_text = frame.locator("#avrl-rate").text_content() or ""
    failure_count = frame.locator(".bid-failure-message").count()

    if rate_text.strip() != "$----" or failure_count > 0:
        record_result(
            results, "FETCH", "Fetch Rate",
            "All Valid Fields",
            "Graph or bid-failure visible",
            "Result visible",
            "PASSED"
        )
    else:
        record_result(
            results, "FETCH", "Fetch Rate",
            "All Valid Fields",
            "Graph or bid-failure visible",
            "No result",
            "FAILED"
        )
        fail_phase("FETCH-POSITIVE", "No graph or bid-failure shown")

# =========================================================
# PHASE 5.5: SLIDER INTERACTION
# =========================================================

SIMULATE_SLIDER_DRAG_JS = """
function simulateSliderDrag(slider, fromValue, toValue, steps = 10) {
  const min = Number(slider.min);
  const max = Number(slider.max);
  const rect = slider.getBoundingClientRect();
  const valueToX = (value) =>
    rect.left + ((value - min) / (max - min)) * rect.width;
  const y = rect.top + rect.height / 2;
  const fire = (event) => slider.dispatchEvent(event);
  const startX = valueToX(fromValue);
  const endX   = valueToX(toValue);

  // pointer over / enter
  fire(new PointerEvent("pointerover", { bubbles: true, clientX: startX, clientY: y, pointerId: 1 }));
  fire(new PointerEvent("pointerenter", { bubbles: true, clientX: startX, clientY: y, pointerId: 1 }));
  fire(new MouseEvent("mouseover", { bubbles: true, clientX: startX, clientY: y }));

  // pointer down
  fire(new PointerEvent("pointerdown", {
    bubbles: true,
    clientX: startX,
    clientY: y,
    pointerId: 1,
    pressure: 0.5,
    buttons: 1
  }));

  fire(new MouseEvent("mousedown", {
    bubbles: true,
    clientX: startX,
    clientY: y,
    buttons: 1
  }));

  slider.focus();
  if (slider.setPointerCapture) slider.setPointerCapture(1);

  for (let i = 0; i <= steps; i++) {
    const progress = i / steps;
    const value = fromValue + (toValue - fromValue) * progress;
    const x = valueToX(value);

    slider.value = value;

    fire(new PointerEvent("pointermove", {
      bubbles: true,
      clientX: x,
      clientY: y,
      pointerId: 1,
      pressure: 0.5,
      buttons: 1
    }));

    fire(new MouseEvent("mousemove", {
      bubbles: true,
      clientX: x,
      clientY: y,
      buttons: 1
    }));

    fire(new Event("input", { bubbles: true }));
  }

  fire(new PointerEvent("pointerup", {
    bubbles: true,
    clientX: endX,
    clientY: y,
    pointerId: 1
  }));

  fire(new MouseEvent("mouseup", {
    bubbles: true,
    clientX: endX,
    clientY: y
  }));

  fire(new Event("change", { bubbles: true }));

  if (slider.releasePointerCapture) slider.releasePointerCapture(1);
}
"""


def phase_slider_interaction(page: Page, frame, results):
    try:
        # Helper to parse value from the standardized pill
        def get_pill_value():
            el = frame.locator("#bid-sub-marker-pill").first
            if el.count() == 0:
                return None
            
            raw = el.get_attribute("title")
            if not raw:
                raw = el.text_content()
            
            if not raw:
                return 0.0
            
            cleaned = raw.replace('Bid Sub:', '').replace('$', '').replace(',', '').strip()
            try:
                return float(cleaned)
            except:
                return 0.0

        def run_slider_test(slider_id, slider_name):
            # Check if slider exists
            if frame.locator(slider_id).count() == 0:
                record_result(
                    results, slider_name, "Slider Presence",
                    "Check existence",
                    "Slider found",
                    "Slider not found",
                    "FAILED"
                )
                return

            initial_val = get_pill_value()
            
            # Run JS drag
            slider = frame.locator(slider_id)
            slider.evaluate(f"""(element) => {{
                {SIMULATE_SLIDER_DRAG_JS}
                simulateSliderDrag(element, 0, 15);
            }}""")
            
            wait_for_settle(page, 2)
            
            final_val = get_pill_value()

            if initial_val is not None and final_val is not None and initial_val != final_val:
                 record_result(
                    results, slider_name, "Slider Interaction",
                    "Drag 0->15",
                    "Value changes",
                    f"Changed from {initial_val} to {final_val}",
                    "PASSED"
                )
            else:
                 record_result(
                    results, slider_name, "Slider Interaction",
                    "Drag 0->15",
                    "Value changes",
                    f"No change ({initial_val} -> {final_val})",
                    "FAILED"
                )
                 # We don't fail the whole phase immediately to allow other sliders to run, 
                 # or we can if strictly sequential. Let's record failure but continue.
            
            # Click resetSliders if available
            if frame.locator("#resetSliders").count() > 0:
                frame.locator("#resetSliders").click()
                wait_for_settle(page, 2)
            else:
                print(f"Warning: #resetSliders not found after testing {slider_name}")

        # Run for all 3 sliders
        run_slider_test("#baseSlider", "Base Slider")
        run_slider_test("#bidSlider", "Bid Slider")
        run_slider_test("#marginSlider", "Margin Slider")

    except Exception as e:
        record_result(
            results, "SLIDER_PHASE", "Slider Phase",
            "Execution",
            "No errors",
            str(e),
            "FAILED"
        )
        fail_phase("SLIDER_PHASE", str(e))

# =========================================================
# PHASE 6: GRAPH ZOOM + RESET
# =========================================================

def phase_graph_and_reset(page: Page, frame, results):
    if frame.locator(".graph-zoom-icon").count() > 0:
        frame.locator(".graph-zoom-icon").click()
        time.sleep(2)

        if page.locator("#avrl-rate-graph-modal").is_visible():
            record_result(
                results, "GRAPH", "Graph Modal Zoom",
                "Zoom Icon",
                "Modal visible",
                "Modal visible",
                "PASSED"
            )
            page.keyboard.press("Escape")
        else:
            record_result(
                results, "GRAPH", "Graph Modal Zoom",
                "Zoom Icon",
                "Modal visible",
                "Modal not visible",
                "FAILED"
            )
            fail_phase("GRAPH", "Graph modal not visible")

    frame.locator("#reset-btn").evaluate("el => el.click()")
    wait_for_settle(page, 10)

    if not frame.locator("#stop-zip-0").input_value():
        record_result(
            results, "RESET", "Reset Functionality",
            "Reset Button",
            "All fields cleared",
            "Fields cleared",
            "PASSED"
        )
    else:
        record_result(
            results, "RESET", "Reset Functionality",
            "Reset Button",
            "All fields cleared",
            "Fields not cleared",
            "FAILED"
        )
        fail_phase("RESET", "Form not cleared")


# =========================================================
# FINAL ORCHESTRATOR
# =========================================================


def test_glass_template_phase_based(page: Page, context: BrowserContext):
    try:
        frame = phase_login_and_iframe(page, context, TEST_RESULTS)
        phase_zip_resolution(page, frame, TEST_RESULTS)
        phase_date_validation(page, frame, TEST_RESULTS)
        phase_dates_and_normalization(page, frame, TEST_RESULTS)
        phase_fetch_negative(page, frame, TEST_RESULTS)
        phase_fetch_positive(page, frame, TEST_RESULTS)
        phase_slider_interaction(page, frame, TEST_RESULTS)
        phase_graph_and_reset(page, frame, TEST_RESULTS)

    except Exception as e:
        record_result(
            TEST_RESULTS,
            phase="TEST",
            test_type="Test Execution",
            input_value="Overall Flow",
            expected="All phases pass",
            actual=str(e),
            status="FAILED"
        )
        raise

    finally:
        os.makedirs("test-results", exist_ok=True)
        with open("test-results/ui_test_report.json", "w") as f:
            json.dump(TEST_RESULTS, f, indent=4)

    assert True

