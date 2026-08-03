# cameras/services.py
import requests
from django.conf import settings
from django.core.cache import cache

TOKEN_CACHE_KEY = "hikconnect:access_token"

class HikConnectError(Exception):
    pass

def get_access_token() -> str:
    token = cache.get(TOKEN_CACHE_KEY)
    if token:
        return token

    resp = requests.post(
        f"{settings.HIKCONNECT_API_BASE}/api/hccgw/platform/v1/token/get",
        data={
            "appKey": settings.HIKCONNECT_APP_KEY,
            "secretKey": settings.HIKCONNECT_APP_SECRET,
        },
        timeout=10,
    )
    data = resp.json()
    if data.get("code") != "200":
        raise HikConnectError(data.get("msg", "token fetch failed"))

    token = data["data"]["accessToken"]
    expire_ms = data["data"].get("expireTime", 0)  # epoch ms, if returned
    # fall back to ~6 days if API doesn't return expireTime
    ttl_seconds = 6 * 24 * 3600
    cache.set(TOKEN_CACHE_KEY, token, timeout=ttl_seconds)
    return token


def get_live_address(device_serial: str, channel_no: str = "1", protocol: str = "2") -> dict:
    """protocol: 1=ezopen, 2=hls, 3=rtmp, 4=flv"""
    token = get_access_token()

    resp = requests.post(
        f"{settings.HIKCONNECT_API_BASE}/api/lapp/v2/live/address/get",
        data={
            "accessToken": token,
            "deviceSerial": device_serial,
            "channelNo": channel_no,
            "protocol": protocol,
        },
        timeout=10,
    )
    data = resp.json()

    if data.get("code") == "10002":  # token expired, refresh once and retry
        cache.delete(TOKEN_CACHE_KEY)
        token = get_access_token()
        resp = requests.post(
            f"{settings.HIKCONNECT_API_BASE}/api/lapp/v2/live/address/get",
            data={
                "accessToken": token,
                "deviceSerial": device_serial,
                "channelNo": channel_no,
                "protocol": protocol,
            },
            timeout=10,
        )
        data = resp.json()

    if data.get("code") != "200":
        raise HikConnectError(data.get("msg", "live address fetch failed"))

    return {"url": data["data"]["url"], "accessToken": token}

CAPTURE_URL = "https://isgp.hikcentralconnect.com/api/hccgw/resource/v1/device/capturePic"

def capture_snapshot(device_serial: str, channel_no: str = "1") -> str:
    """Returns a temporary signed URL (~15 min validity) to the captured JPEG."""
    token = get_access_token()

    resp = requests.post(
        CAPTURE_URL,
        json={"deviceSerial": device_serial, "channelNo": int(channel_no)},
        headers={"Authorization": token},  # confirm exact header/param name in your Team OpenAPI docs
        timeout=15,
    )
    data = resp.json()

    if data.get("errorCode") != "0":
        raise HikConnectError(data.get("msg", f"capture failed: {data}"))
    if data["data"].get("isEncrypted"):
        raise HikConnectError("Encrypted capture not supported yet")

    return data["data"]["captureUrl"]