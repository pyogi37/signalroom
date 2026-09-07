from pathlib import Path

from playwright.sync_api import sync_playwright


output = Path(__file__).resolve().parents[1] / "outputs" / "signalroom-demo.png"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
    errors = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.goto("http://127.0.0.1:5173", wait_until="domcontentloaded")
    page.get_by_text("Review the proposal for", exact=False).wait_for(timeout=30_000)
    assert page.get_by_text("Review the proposal for", exact=False).is_visible()
    assert page.get_by_role("heading", name="Requirements").is_visible()
    page.get_by_role("button", name="Analyze new discovery").click()
    assert page.get_by_role("dialog", name="Analyze new discovery").is_visible()
    page.get_by_role("button", name="Record discovery").click()
    assert page.get_by_text("Voice adapter is ready.", exact=False).is_visible()
    page.locator('input[type="file"]').set_input_files({
        "name": "synthetic-reference.md",
        "mimeType": "text/markdown",
        "buffer": b"Synthetic exception policy. Every shipment alert must retain the source event and a named reviewer for audit.",
    })
    page.get_by_role("button", name="Analyze discovery", exact=True).click()
    page.get_by_text("Atlas Distribution", exact=True).wait_for(timeout=10_000)
    assert page.get_by_text("Retrieved knowledge").is_visible()
    page.get_by_role("button", name="REQ-02").click()
    assert page.get_by_role("heading", name="Detect and surface operational exceptions").is_visible()
    page.get_by_role("button", name="Request changes").click()
    page.get_by_role("heading", name="Brief returned for revision").wait_for(timeout=10_000)
    assert page.get_by_text("Approval is unavailable until the brief returns to review.", exact=False).is_visible()
    first_answer = page.locator('.question input').first
    first_answer.fill('The sponsor approved a two-week baseline with a named operations owner.')
    page.get_by_role("button", name="Add answers and re-run").click()
    page.get_by_text("Follow-up evidence added and the solution graph re-ran.").wait_for(timeout=10_000)
    page.get_by_role("button", name="Approve brief").click()
    page.get_by_role("heading", name="Brief approved").wait_for(timeout=10_000)
    assert page.get_by_text("Grounded requirements", exact=True).is_visible()
    assert page.locator('.question input').first.is_disabled()
    with page.expect_download() as download_info:
        page.get_by_role("link", name="Export brief").click()
    assert download_info.value.suggested_filename.endswith(".docx")
    page.screenshot(path=str(output), full_page=True)
    assert not errors, errors
    print(f"PASS screenshot={output}")
    browser.close()
