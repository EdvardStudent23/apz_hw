import os, time, uuid, random, asyncio, uvicorn, httpx
import hazelcast
from fastapi import FastAPI, Body, HTTPException
from contextlib import asynccontextmanager

CONFIG_SERVER = os.getenv("CONFIG_SERVER_URL", "http://config-server:9000")
MY_URL        = os.getenv("MY_URL",            "http://facade-service:8000")
HZ_MEMBERS    = os.getenv("HZ_MEMBERS",        "hz1:5701,hz2:5701,hz3:5701")

hz_client = hazelcast.HazelcastClient(
    cluster_members=HZ_MEMBERS.split(","),
    cluster_name="dev",
)
mq = hz_client.get_queue("transactions_queue").blocking()

metrics = {"logging": 0.0, "counter_enqueue": 0.0}


async def resolve(service_name: str) -> str:
    """Query config-server for registered URLs of service_name, pick one at random."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{CONFIG_SERVER}/services/{service_name}", timeout=3.0)
    urls: list = r.json().get("urls", [])
    if not urls:
        raise HTTPException(
            status_code=503,
            detail=f"No instances registered for {service_name!r}",
        )
    chosen = random.choice(urls)
    print(f"[facade] resolved {service_name!r} -> {chosen}", flush=True)
    return chosen


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{CONFIG_SERVER}/register",
                json={"name": "facade-service", "url": MY_URL},
                timeout=5.0,
            )
        except Exception as exc:
            print(f"[facade] registration failed: {exc}", flush=True)
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/process")
async def handle_post(data: dict = Body(...)):
    t_id    = str(uuid.uuid4())
    payload = {**data, "transaction_id": t_id}

    log_url   = await resolve("logging-service")
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
    print(f"[facade] enqueued transaction {t_id}", flush=True)

    return {"transaction_id": t_id, "status": "queued"}


@app.get("/user/{user_id}")
async def get_user(user_id: str):
    log_url = await resolve("logging-service")
    cnt_url = await resolve("counter-service")

    async with httpx.AsyncClient() as client:
        b = await client.get(f"{cnt_url}/balance/{user_id}", timeout=3.0)
        t = await client.get(f"{log_url}/logs/{user_id}",   timeout=3.0)

    balance = b.json().get("balance") if b.is_success else None
    return {"balance": balance, "transactions": t.json()}


@app.get("/accounts")
async def get_accounts():
    cnt_url = await resolve("counter-service")
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{cnt_url}/balances", timeout=3.0)
    return res.json()


@app.get("/stats")
async def get_stats():
    return metrics


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
