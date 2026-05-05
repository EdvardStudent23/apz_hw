"""
logging-service/main.py
"""
import os, logging, uvicorn, hazelcast
from fastapi import FastAPI, Body, HTTPException
from contextlib import asynccontextmanager
from consul_helper import kv_get, register_service, deregister_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MY_URL       = os.getenv("MY_URL",       "http://logging-1:8000")
SERVICE_NAME = os.getenv("SERVICE_NAME", "logging-service")

hz_client       = None
distributed_map = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global hz_client, distributed_map

    register_service(name=SERVICE_NAME, my_url=MY_URL, health_path="/health")
    logger.info(f"[{SERVICE_NAME} @ {MY_URL}] registered in Consul")

    hz_members  = kv_get("config/hazelcast/members",      "hz1:5701,hz2:5701,hz3:5701")
    hz_cluster  = kv_get("config/hazelcast/cluster-name", "dev")
    hz_map_name = kv_get("config/hazelcast/map-name",     "logs_map")
    logger.info(f"[{SERVICE_NAME}] KV → cluster={hz_cluster!r} members={hz_members} map={hz_map_name!r}")

    hz_client       = hazelcast.HazelcastClient(cluster_members=hz_members.split(","), cluster_name=hz_cluster)
    distributed_map = hz_client.get_map(hz_map_name).blocking()
    logger.info(f"[{SERVICE_NAME}] Hazelcast ready, map={hz_map_name!r}")

    yield

    deregister_service()
    hz_client.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok", "service": SERVICE_NAME, "instance": MY_URL}

@app.post("/log")
async def log_transaction(data: dict = Body(...)):
    if distributed_map is None:
        raise HTTPException(status_code=503, detail="Hazelcast not ready")
    t_id = data.get("transaction_id")
    distributed_map.put(t_id, data)
    logger.info(f"[{SERVICE_NAME} @ {MY_URL}] stored {t_id}")
    return {"status": "ok"}

@app.get("/logs")
async def get_all_logs():
    if distributed_map is None:
        raise HTTPException(status_code=503, detail="Hazelcast not ready")
    return list(distributed_map.values())

@app.get("/logs/{user_id}")
async def get_user_logs(user_id: str):
    if distributed_map is None:
        raise HTTPException(status_code=503, detail="Hazelcast not ready")
    return [msg for msg in distributed_map.values() if str(msg.get("user_id")) == user_id]

if __name__ == "__main__":
    port = int(MY_URL.rsplit(":", 1)[-1])
    uvicorn.run(app, host="0.0.0.0", port=port)
