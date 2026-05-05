"""
consul_helper.py — Shared module for service management.
- Service registration and health checks
- Service discovery (resolve)
- KV configuration retrieval
"""

import os
import time
import random
import logging
import uuid
import consul

logger = logging.getLogger(__name__)

CONSUL_HOST = os.getenv("CONSUL_HOST", "localhost")
CONSUL_PORT = int(os.getenv("CONSUL_PORT", "8500"))


def _client() -> consul.Consul:
    return consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)


def kv_get(key: str, default: str = "", retries: int = 15, delay: float = 2.0) -> str:
    """Fetches value from Consul KV with retries for startup synchronization."""
    c = _client()
    for attempt in range(retries):
        try:
            _, data = c.kv.get(key)
            if data and data["Value"]:
                value = data["Value"].decode("utf-8")
                logger.info(f"[Consul KV] {key} = {value!r}")
                return value
        except Exception as e:
            logger.warning(f"[Consul KV] attempt {attempt+1}/{retries} error: {e}")
        
        logger.warning(f"[Consul KV] key '{key}' not ready, retry {attempt+1}/{retries}")
        time.sleep(delay)
    
    logger.error(f"[Consul KV] '{key}' not found after {retries} attempts, using default={default!r}")
    return default


_service_id: str | None = None


def register_service(name: str, my_url: str, health_path: str = "/health") -> str:
    """Registers the service instance in Consul."""
    global _service_id

    without_scheme = my_url.replace("http://", "").replace("https://", "")
    host, port_str = without_scheme.rsplit(":", 1)
    port = int(port_str)

    _service_id = f"{name}-{uuid.uuid4().hex[:8]}"

    c = _client()
    check = consul.Check.http(
        url=f"{my_url}{health_path}",
        interval="10s",
        timeout="5s",
        deregister="30s",
    )

    c.agent.service.register(
        name=name,
        service_id=_service_id,
        address=host,
        port=port,
        check=check,
        tags=[name, "python", "fastapi"],
    )
    logger.info(f"[Consul] Registered '{name}' as '{_service_id}' at {host}:{port}")
    return _service_id


def deregister_service():
    """Removes registration on shutdown."""
    if _service_id:
        try:
            _client().agent.service.deregister(_service_id)
            logger.info(f"[Consul] Deregistered '{_service_id}'")
        except Exception as e:
            logger.error(f"[Consul] Deregister error: {e}")


# ── SERVICE DISCOVERY ────────────────────────────────────────
def resolve(service_name: str) -> str:
    """Returns a random healthy service instance URL."""
    c = _client()
    _, services = c.health.service(service_name, passing=True)

    urls = [
        f"http://{s['Service']['Address']}:{s['Service']['Port']}"
        for s in services
    ]

    if not urls:
        raise RuntimeError(f"No healthy instances of '{service_name}' in Consul")

    chosen = random.choice(urls)
    logger.info(f"[Consul] Resolved '{service_name}' -> {chosen} (from {len(urls)} instances)")
    return chosen