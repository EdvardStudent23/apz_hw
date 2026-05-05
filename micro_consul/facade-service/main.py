"""
facade-service/main.py
"""
import os, time, uuid, logging, asyncio, uvicorn, httpx, hazelcast
from fastapi import FastAPI, Body, HTTPException
from contextlib import asynccontextmanager
from consul_helper import kv_get, register_service, deregister_service, resolve

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MY_URL       = os.getenv("MY_URL",       "http://facade-service-1:8000")
SERVICE_NAME = os.getenv("SERVICE_NAME", "facade-service")

hz_client = None
mq        = None
metrics   = {"logging": 0.0, "counter_enqueue": 0.0}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global hz_client, mq

    register_service(name=SERVICE_NAME, my_url=MY_URL, health_path="/health")
    logger.info(f"[{SERVICE_NAME} @ {MY_URL}] registered in Consul")

    mq_members    = kv_get("config/mq/members",      "hz1:5701,hz2:5701,hz3:5701")
    mq_cluster    = kv_get("config/mq/cluster-name", "dev")
    mq_queue_name = kv_get("config/mq/queue-name",   "transactions_queue")
    logger.info(f"[{SERVICE_NAME}] KV → queue={mq_queue_name!r} cluster={mq_cluster!r} members={mq_members}")

    hz_client = hazelcast.HazelcastClient(cluster_members=mq_members.split(","), cluster_name=mq_cluster)
    mq        = hz_client.get_queue(mq_queue_name).blocking()
    logger.info(f"[{SERVICE_NAME}] Hazelcast MQ ready, queue={mq_queue_name!r}")

    yield

    deregister_service()
    hz_client.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok", "service": SERVICE_NAME, "instance": MY_URL}

@app.post("/process")
async def handle_post(data: dict = Body(...)):
    if mq is None:
        raise HTTPException(status_code=503, detail="MQ not ready")

    t_id    = str(uuid.uuid4())
    payload = {**data, "transaction_id": t_id}

    try:
        log_url = resolve("logging-service")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    start_log = time.time()
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{log_url}/log", json=payload, timeout=2.0)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Logging failed: {exc}")
    metrics["logging"] += time.time() - start_log

    start_enq = time.time()
    await asyncio.to_thread(mq.put, payload)
    metrics["counter_enqueue"] += time.time() - start_enq

    logger.info(f"[{SERVICE_NAME} @ {MY_URL}] enqueued {t_id}")
    return {"transaction_id": t_id, "status": "queued"}

@app.get("/user/{user_id}")
async def get_user(user_id: str):

    try:
        log_url = resolve("logging-service")
        cnt_url = resolve("counter-service")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    async with httpx.AsyncClient() as client:
        b = await client.get(f"{cnt_url}/balance/{user_id}", timeout=3.0)
        t = await client.get(f"{log_url}/logs/{user_id}",   timeout=3.0)

    return {"balance": b.json().get("balance") if b.is_success else None,
            "transactions": t.json()}

@app.get("/accounts")
async def get_accounts():
    try:
        cnt_url = resolve("counter-service")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{cnt_url}/balances", timeout=3.0)
    return res.json()

@app.get("/stats")
async def get_stats():
    return metrics

if __name__ == "__main__":
    port = int(MY_URL.rsplit(":", 1)[-1])
    uvicorn.run(app, host="0.0.0.0", port=port)
