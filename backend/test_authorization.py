
import json
import uuid
import os
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

# Enter the key privately.

# Read the local test key from the environment.
API_KEY = os.environ.get("API_KEY")

if not API_KEY:
    raise SystemExit(
        "API_KEY is not set. Configure it in PowerShell first."
    )



def send_request(method, path, headers=None, payload=None):
    data = None

    request_headers = {
        "Accept": "application/json"
    }

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    if headers:
        request_headers.update(headers)

    request = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers=request_headers,
        method=method,
    )

    
    # Bypass system proxy for local FastAPI testing
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({})
    )

    try:
        with opener.open(
            request, timeout=120
        ) as response:

            status = response.status
            raw = response.read()

    except urllib.error.HTTPError as error:
        status = error.code
        raw = error.read()

    try:
        body = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        body = {}

    return status, body


correct_key = {"X-API-Key": API_KEY}

wrong_key = {"X-API-Key": "intentionally-invalid-key"}

bearer_key = {
    "Authorization": f"Bearer {API_KEY}"
}

ticket = {
    "ticket_id": "AUTH-TEST-001",
    "channel": "email",
    "subject": "Refund request",
    "text": "I was charged twice and need a refund."
}

batch = {
    "tickets": [ticket]
}

unknown_id = str(uuid.uuid4())

tests = [
    ("Public health", "GET", "/health", None, None, 200),

    ("Predict without key", "POST", "/predict",
     None, ticket, 401),

    ("Predict with wrong key", "POST", "/predict",
     wrong_key, ticket, 401),

    ("Predict with correct key", "POST", "/predict",
     correct_key, ticket, 200),

    ("Predict with Bearer key", "POST", "/predict",
     bearer_key, ticket, 200),

    ("Batch without key", "POST", "/predict/batch",
     None, batch, 401),

    ("Batch with correct key", "POST", "/predict/batch",
     correct_key, batch, 200),

    ("Job submission without key", "POST", "/batch/jobs",
     None, {}, 401),

    ("Job submission with key, invalid body",
     "POST", "/batch/jobs", correct_key, {}, 422),

    ("Job status without key",
     "GET", f"/batch/jobs/{unknown_id}",
     None, None, 401),

    ("Unknown job status with key",
     "GET", f"/batch/jobs/{unknown_id}",
     correct_key, None, 404),

    ("Job results without key",
     "GET", f"/batch/jobs/{unknown_id}/results",
     None, None, 401),

    ("Unknown job results with key",
     "GET", f"/batch/jobs/{unknown_id}/results",
     correct_key, None, 404),
]

passed = 0

print("\nTensorForge 2.0 - API Authorization Tests")
print("=" * 65)

for name, method, path, headers, payload, expected in tests:
    try:
        actual, body = send_request(
            method, path, headers, payload
        )

        valid_error = (
            actual != 401 or (
                isinstance(body.get("error"), dict)
                and body["error"].get("code") == "UNAUTHORIZED"
            )
        )

        success = actual == expected and valid_error

        if success:
            passed += 1

        result = "PASS" if success else "FAIL"

        print(
            f"[{result}] {name} "
            f"(expected {expected}, got {actual})"
        )

        if not success:
            print("  Response:", body)

    except Exception as error:
        print(f"[FAIL] {name}: {type(error).__name__}")

print("=" * 65)
print(f"Tests passed: {passed}/{len(tests)}")

if passed == len(tests):
    print("AUTHORIZATION TESTS PASSED")
else:
    print("AUTHORIZATION TESTS NEED ATTENTION")
    raise SystemExit(1)
