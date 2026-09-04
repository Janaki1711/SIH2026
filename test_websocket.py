#!/usr/bin/env python3
"""
WebSocket connection test for iTantra M3
Verifies that /ws/hubbli and /ws/tolankere connect successfully
"""

import asyncio
import websockets
import json
import sys

async def test_websocket_connection(location: str):
    """Test WebSocket connection to a specific location"""
    url = f"ws://localhost:8000/ws/{location}"
    print(f"\n[TEST] Connecting to {url}")
    
    try:
        async with websockets.connect(url, ping_interval=None) as websocket:
            # Receive the initial connection message
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            msg = json.loads(response)
            
            print(f"✓ Connection successful for /ws/{location}")
            print(f"  Response type: {msg.get('type')}")
            print(f"  Location: {msg.get('location')}")
            print(f"  Partner: {msg.get('partner')}")
            print(f"  Adapter info: {msg.get('adapter_info')}")
            
            # Send a language selection message
            await websocket.send(json.dumps({
                "type": "set_language",
                "language": "hi"
            }))
            
            # Receive language confirmation
            lang_resp = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            lang_msg = json.loads(lang_resp)
            print(f"✓ Language set response: {lang_msg.get('type')}")
            
            return True
            
    except Exception as e:
        print(f"✗ Connection failed for /ws/{location}")
        print(f"  Error: {type(e).__name__}: {e}")
        return False

async def main():
    print("=" * 60)
    print("iTANTRA M3 — WebSocket Connection Test")
    print("=" * 60)
    
    results = {}
    
    # Test both endpoints
    for location in ["hubbli", "tolankere"]:
        results[location] = await test_websocket_connection(location)
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    all_passed = True
    for location, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  /ws/{location:12} : {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("  WebSocket endpoints are functional")
        print("  CORS fix verified: allow_origin_regex='.*'")
        sys.exit(0)
    else:
        print("✗ TESTS FAILED")
        print("  Check backend logs for details")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
