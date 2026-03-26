from __future__ import annotations

import ipaddress
import socket
from collections.abc import Iterable


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _discover_local_host_candidates() -> list[str]:
    candidates = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        socket.gethostname(),
        socket.getfqdn(),
    }

    for name in tuple(candidates):
        if not name:
            continue
        try:
            for info in socket.getaddrinfo(name, None):
                address = info[4][0].split("%", 1)[0]
                candidates.add(address)
        except OSError:
            continue

    return _ordered_unique(candidates)


def expand_local_dev_hosts(hosts: Iterable[str], *, debug: bool) -> list[str]:
    base_hosts = _ordered_unique(hosts)
    if not debug:
        return base_hosts
    return _ordered_unique([*base_hosts, *_discover_local_host_candidates()])


def _format_origin_host(host: str) -> str:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return host
    if address.version == 6:
        return f"[{host}]"
    return host


def build_local_dev_csrf_trusted_origins(
    origins: Iterable[str],
    *,
    allowed_hosts: Iterable[str],
    debug: bool,
    dev_ports: Iterable[int] = (8000,),
) -> list[str]:
    base_origins = _ordered_unique(origins)
    if not debug:
        return base_origins

    extra_origins: list[str] = []
    ports = tuple(dev_ports)
    for host in allowed_hosts:
        host = str(host).strip()
        if not host or host == "*" or host.startswith(".") or "*" in host:
            continue
        formatted_host = _format_origin_host(host)
        for scheme in ("http", "https"):
            extra_origins.append(f"{scheme}://{formatted_host}")
            for port in ports:
                extra_origins.append(f"{scheme}://{formatted_host}:{port}")

    return _ordered_unique([*base_origins, *extra_origins])
