"""Asynchronous network crawling with strict SSRF and DoS guards."""

import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 "
        "(compatible; ProspectsRadarBot/1.0; +https://prospectsradar.io/bot)"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}

AI_TARGET_BOTS = {
    "gptbot",
    "chatgpt-user",
    "claudebot",
    "anthropic-ai",
    "perplexitybot",
    "google-extended",
}

_NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")
_RESERVED_HOST_SUFFIXES = (".local", ".internal", ".localhost", ".home.arpa")
_RESERVED_HOST_PREFIXES = ("metadata.", "kubernetes.", "kube-", "rancher-meta")


def normalize_scan_url(raw_url: str) -> str:
    """Validate and normalize a scan target URL before any network connection."""
    raw = raw_url.strip()
    if not raw:
        raise ValueError("URL vide.")
    if len(raw) > 2048:
        raise ValueError("URL trop longue (max 2048 caractères).")
    if any(c.isspace() for c in raw):
        raise ValueError("L'URL ne doit pas contenir d'espaces.")
    if not (raw.lower().startswith("http://") or raw.lower().startswith("https://")):
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if not host or (host != "localhost" and "." not in host and ":" not in host):
        raise ValueError("Hôte manquant ou invalide.")
    return raw


def is_nonpublic_ip(ip_str: str) -> bool:
    """True if the IP is private, reserved, loopback, or internal."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    if ip.version == 6 and ip in _NAT64_PREFIX:
        embedded_v4 = ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
        return is_nonpublic_ip(str(embedded_v4))
    return (
        not ip.is_global
        or ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def assert_target_safe(url: str) -> None:
    """Ensure target hostname does not resolve to private or internal networks."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip().lower()
    if host in ("localhost", "localhost."):
        raise ValueError("Hôte interdit (localhost).")
    if host.startswith(_RESERVED_HOST_PREFIXES) or host.endswith(_RESERVED_HOST_SUFFIXES):
        raise ValueError("Hôte réservé / réseau interne interdit.")

    try:
        ipaddress.ip_address(host)
        if is_nonpublic_ip(host):
            raise ValueError("Adresse IP privée ou réservée interdite.")
    except ValueError:
        pass

    try:
        resolved = socket.getaddrinfo(host, None)
        for entry in resolved:
            ip_str = entry[4][0]
            if is_nonpublic_ip(ip_str):
                raise ValueError("Résolution DNS vers une IP privée ou réservée.")
    except (socket.gaierror, OSError):
        pass


def parse_robots_txt(content: str) -> tuple[list[str], bool]:
    """Parse robots.txt to detect AI bot restrictions."""
    disallowed_bots: set[str] = set()
    global_disallowed = False
    current_agents: list[str] = []
    current_disallow_all = False
    in_directives = False

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().lower()
        val = val.strip()

        if key == "user-agent":
            if in_directives:
                if current_disallow_all:
                    if "*" in current_agents:
                        global_disallowed = True
                    for b in current_agents:
                        if b in AI_TARGET_BOTS:
                            disallowed_bots.add(b)
                current_disallow_all = False
                current_agents = []
                in_directives = False
            current_agents.append(val.lower())
        elif key == "disallow":
            in_directives = True
            if val in ("/", "/*") or val.startswith("/ "):
                current_disallow_all = True
        elif key == "allow":
            in_directives = True
            if val in ("/", "/*"):
                current_disallow_all = False

    if current_disallow_all:
        if "*" in current_agents:
            global_disallowed = True
        for b in current_agents:
            if b in AI_TARGET_BOTS:
                disallowed_bots.add(b)

    return sorted(list(disallowed_bots)), global_disallowed


async def fetch_robots_info(client: httpx.AsyncClient, domain: str, scheme: str = "https") -> dict[str, Any]:
    """Fetch and parse robots.txt for AI crawlers."""
    url = f"{scheme}://{domain}/robots.txt"
    try:
        resp = await client.get(url, timeout=5.0)
        if resp.status_code == 200:
            disallowed, is_all = parse_robots_txt(resp.text)
            return {
                "found": True,
                "disallowed_bots": disallowed,
                "global_disallowed": is_all,
                "raw": resp.text[:500],
            }
    except Exception:
        pass
    return {"found": False, "disallowed_bots": [], "global_disallowed": False, "raw": ""}


async def fetch_llms_info(client: httpx.AsyncClient, domain: str, scheme: str = "https") -> dict[str, Any]:
    """Check for presence of llms.txt standard files."""
    for path in ["/.well-known/llms.txt", "/llms.txt"]:
        url = f"{scheme}://{domain}{path}"
        try:
            resp = await client.get(url, timeout=4.0)
            if resp.status_code == 200 and len(resp.text) > 30:
                return {"found": True, "path": path, "content": resp.text[:600]}
        except Exception:
            continue
    return {"found": False, "path": None, "content": None}


async def fetch_web_page(
    client: httpx.AsyncClient, url: str, max_bytes: int = 2_000_000
) -> tuple[int, dict[str, str], str]:
    """Fetch webpage HTML with size bounds and safe redirect tracking."""
    assert_target_safe(url)
    resp = await client.get(url)
    if hasattr(resp, "history"):
        for r in resp.history:
            assert_target_safe(str(r.url))
    if hasattr(resp, "url"):
        assert_target_safe(str(resp.url))

    content_bytes = resp.content[:max_bytes]
    text = content_bytes.decode("utf-8", errors="replace")
    headers_dict = {k.lower(): v for k, v in resp.headers.items()}
    return resp.status_code, headers_dict, text
