import json
import os

from playwright.sync_api import expect

UI_BASE_URL = os.getenv("WEB_UI_BASE_URL", "http://localhost:7002")


def _build_settings_payload(provider: str) -> dict:
    """Return a minimal mock settings payload matching the speech section shape."""
    realtime_hidden = provider != "openai_realtime"

    return {
        "settings": {
            "title": "Settings",
            "buttons": [
                {"id": "save", "title": "Save", "classes": "btn btn-ok"},
                {
                    "id": "cancel",
                    "title": "Cancel",
                    "type": "secondary",
                    "classes": "btn btn-cancel",
                },
            ],
            "sections": [
                {
                    "id": "speech",
                    "title": "Speech",
                    "description": "Voice configuration",
                    "tab": "agent",
                    "fields": [
                        {
                            "id": "speech_provider",
                            "title": "Speech provider",
                            "type": "select",
                            "value": provider,
                            "options": [
                                {"value": "browser", "label": "Browser"},
                                {"value": "openai_realtime", "label": "OpenAI Realtime"},
                            ],
                        },
                        {
                            "id": "speech_realtime_model",
                            "title": "Realtime model",
                            "type": "text",
                            "value": "gpt-4o-realtime-preview",
                            "hidden": realtime_hidden,
                        },
                        {
                            "id": "speech_realtime_voice",
                            "title": "Realtime voice",
                            "type": "text",
                            "value": "verse",
                            "hidden": realtime_hidden,
                        },
                        {
                            "id": "speech_realtime_endpoint",
                            "title": "Realtime session endpoint",
                            "type": "text",
                            "value": "https://api.openai.com/v1/realtime/sessions",
                            "hidden": realtime_hidden,
                        },
                    ],
                }
            ],
        }
    }


def test_realtime_provider_requests_openai_session(page):
    """Ensure selecting OpenAI Realtime issues a session request with the configured fields."""

    page.add_init_script(
        """
(() => {
  class FakeRTCDataChannel {
    constructor() {
      this.readyState = 'open';
      this._listeners = {};
    }
    addEventListener(type, callback) {
      this._listeners[type] = callback;
      if (type === 'open') {
        setTimeout(() => callback({}), 0);
      }
    }
    send() {}
    close() {}
  }

  class FakeRTCPeerConnection {
    constructor() {
      this.connectionState = 'connected';
      this._listeners = {};
    }
    addEventListener(type, callback) {
      this._listeners[type] = callback;
    }
    addTransceiver() {}
    createDataChannel() {
      this._dataChannel = new FakeRTCDataChannel();
      return this._dataChannel;
    }
    async createOffer() {
      return { type: 'offer', sdp: 'fake-offer' };
    }
    async setLocalDescription() {}
    async setRemoteDescription() {
      const listener = this._listeners['connectionstatechange'];
      if (listener) {
        setTimeout(() => listener({ target: this }), 0);
      }
    }
    close() {
      this.connectionState = 'closed';
    }
  }

  window.RTCPeerConnection = FakeRTCPeerConnection;
})();
        """
    )

    settings_state = {"provider": "browser"}

    def fulfill_json(route, payload):
        route.fulfill(
            status=200,
            headers={"content-type": "application/json"},
            body=json.dumps(payload),
        )

    # No CSRF route: UI does not use CSRF in Gateway flow

    def handle_settings_get(route, _request):
        fulfill_json(route, _build_settings_payload(settings_state["provider"]))

    page.route("**/settings_get", handle_settings_get)

    def handle_settings_set(route, request):
        payload = json.loads(request.post_data or "{}")
        for section in payload.get("sections", []):
            for field in section.get("fields", []):
                if field.get("id") == "speech_provider":
                    settings_state["provider"] = field.get("value", settings_state["provider"])
        fulfill_json(route, {"settings": payload})

    page.route("**/settings_set", handle_settings_set)

    realtime_payloads: list[dict] = []

    def handle_realtime_session(route, request):
        if request.method.upper() == "POST":
            try:
                realtime_payloads.append(json.loads(request.post_data or "{}"))
            except json.JSONDecodeError:
                realtime_payloads.append({})

        fulfill_json(
            route,
            {
                "session": {
                    "client_secret": {"value": "test-secret"},
                    "model": "gpt-4o-realtime-preview",
                }
            },
        )

    page.route("**/realtime_session", handle_realtime_session)

    page.goto(UI_BASE_URL)

    settings_button = page.locator("#settings")
    expect(settings_button).to_be_visible()
    settings_button.click()

    modal = page.locator("#settingsModal")
    expect(modal).to_be_visible()

    expect(modal.get_by_text("Realtime model")).to_have_count(0)

    provider_select = modal.locator("select").first
    provider_select.select_option("openai_realtime")

    expect(modal.get_by_text("Realtime model")).to_be_visible()

    with page.expect_request("**/settings_set"):
        modal.get_by_role("button", name="Save").click()

    page.wait_for_selector("#settingsModal", state="hidden")

    page.wait_for_function(
        "() => window.Alpine && window.Alpine.store('speech')?.speech_provider === 'openai_realtime'"
    )

    with page.expect_request("**/realtime_session"):
        page.evaluate(
            "async () => { await window.Alpine.store('speech').ensureRealtimeConnection(); }"
        )

    assert realtime_payloads, "Realtime session request was not sent"
    request_payload = realtime_payloads[0]
    assert request_payload.get("model") == "gpt-4o-realtime-preview"
    assert request_payload.get("voice") == "verse"
    assert (
        request_payload.get("endpoint") == "https://api.openai.com/v1/realtime/sessions"
    ), "Unexpected realtime endpoint"
