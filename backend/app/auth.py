import hmac
import os

from dotenv import load_dotenv


load_dotenv()


def get_api_keys_from_headers(headers) -> list[str]:
    keys = []

    # --------------------------------------------------------
    # X-API-Key
    # --------------------------------------------------------
    x_api_key = headers.get("x-api-key")

    if x_api_key:
        keys.append(x_api_key)

    # --------------------------------------------------------
    # Authorization: Bearer <key>
    # --------------------------------------------------------
    authorization = headers.get("authorization")

    if authorization:
        scheme, _, token = authorization.partition(" ")

        if scheme.lower() == "bearer" and token:
            keys.append(token)

    return keys


def get_api_key_from_headers(
    headers,
) -> str | None:
    keys = get_api_keys_from_headers(headers)

    if not keys:
        return None

    return keys[0]


def verify_api_key_value(
    provided_key: str | None,
) -> bool:
    expected_key = os.getenv("API_KEY")

    if not expected_key:
        return False

    if not provided_key:
        return False

    return hmac.compare_digest(
        provided_key,
        expected_key,
    )


def verify_api_key_headers(headers) -> bool:
    expected_key = os.getenv("API_KEY")

    if not expected_key:
        return False

    provided_keys = get_api_keys_from_headers(
        headers
    )

    for provided_key in provided_keys:
        if hmac.compare_digest(
            provided_key,
            expected_key,
        ):
            return True

    return False