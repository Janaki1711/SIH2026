"""
E2E smoke test: two users, different languages, real HTTP + WebSocket.

Flow:
  1. Register/login user A (Hindi) and user B (Tamil) via OTP endpoints.
  2. A creates a conversation with B.
  3. Both connect to /api/chat/{token}.
  4. A sends a Hindi message over the WebSocket.
  5. Assert B receives it live with a Tamil translated_text.

Run:  .venv/bin/python e2e_chat_smoke.py
"""
import json
import sys

from fastapi.testclient import TestClient

import main  # FastAPI app (also runs database.init_db())

client = TestClient(main.app)


def login(phone: str, name: str, lang: str) -> tuple[str, dict]:
    r = client.post("/api/auth/send-otp",
                    json={"phone": phone, "captcha_token": "e2e"})
    assert r.status_code == 200, r.text
    otp = r.json()["otp_for_demo"]

    r = client.post("/api/auth/verify-otp", json={"phone": phone, "otp": otp})
    assert r.status_code == 200, r.text
    token = r.json()["session_token"]

    r = client.post("/api/auth/setup-profile",
                    json={"token": token, "display_name": name,
                          "preferred_language": lang})
    assert r.status_code == 200, r.text
    profile = r.json()["profile"]
    return token, profile


def main_flow() -> None:
    token_a, prof_a = login("1111111111", "Alpha Hindi", "hi")
    token_b, prof_b = login("2222222222", "Beta Tamil", "ta")
    print(f"[1] logged in: A={prof_a['display_name']}({prof_a['preferred_language']}) "
          f"B={prof_b['display_name']}({prof_b['preferred_language']})")

    # Conversation
    r = client.post("/api/conversations",
                    json={"target_user_id": prof_b["id"]},
                    headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200, r.text
    conv_id = r.json()["conversation_id"]
    print(f"[2] conversation created: {conv_id}")

    with client.websocket_connect(f"/api/chat/{token_a}") as ws_a, \
         client.websocket_connect(f"/api/chat/{token_b}") as ws_b:
        hello_a = ws_a.receive_json()
        hello_b = ws_b.receive_json()
        assert hello_a["type"] == "connected" and hello_b["type"] == "connected"
        print(f"[3] both websockets connected")

        ws_a.send_json({"type": "subscribe", "conversation_id": conv_id})
        sub = ws_a.receive_json()
        assert sub["type"] == "subscribed", sub
        print(f"[4] subscribe acked")

        hindi_text = "हब्बली में तुरंत एक बचाव दल भेजो"
        ws_a.send_json({"type": "message", "conversation_id": conv_id,
                        "text": hindi_text, "priority": 1})

        # A first gets its own new_message broadcast, then the delivery ack
        # (order is not guaranteed, so drain until the ack arrives).
        ack = None
        for _ in range(10):
            m = ws_a.receive_json()
            if m["type"] == "message_delivered":
                ack = m
                break
        assert ack is not None, "no message_delivered ack for sender"
        print(f"[5] sender ack: {ack['type']}")

        recv_b = ws_b.receive_json()
        assert recv_b["type"] == "new_message", recv_b
        assert recv_b["original_text"] == hindi_text
        translated = recv_b["translated_text"]
        print(f"[6] B received: original={hindi_text!r}")
        print(f"              translated({prof_b['preferred_language']})={translated!r}")

        # Semantic payload must be present and parseable
        sem = json.loads(recv_b["semantic_payload"])
        assert sem, "semantic payload empty"
        print(f"[7] semantic payload: action={sem.get('action')} urgency={sem.get('urgency')}")

        # Cross-language sanity: Tamil output must contain Tamil script,
        # and must NOT be the untouched Hindi passthrough.
        tamil_chars = sum(1 for c in translated if '\u0b80' <= c <= '\u0bff')
        hindi_chars = sum(1 for c in translated if '\u0900' <= c <= '\u097f')
        assert translated != hindi_text, "translation was a passthrough!"
        assert tamil_chars > 0, f"no Tamil script in: {translated!r}"
        assert "unknown" not in translated.lower(), "sentinel leaked"
        print(f"[8] translation verified: {tamil_chars} Tamil chars, "
              f"{hindi_chars} residual Hindi chars — PASS")

    print("\nE2E CHAT SMOKE: ALL PASS")


if __name__ == "__main__":
    try:
        main_flow()
    except Exception as e:
        print(f"\nE2E CHAT SMOKE: FAIL — {e!r}")
        sys.exit(1)
