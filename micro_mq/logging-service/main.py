import os, uvicorn, httpx
import hazelcast
from fastapi import FastAPI, Body
from contextlib import asynccontextmanager

CONFIG_SERVER = os.getenv("CONFIG_SERVER_URL", "http://config-server:9000")
MY_URL        = os.getenv("MY_URL",            "http://logging-1:8000")
HZ_MEMBERS    = os.getenv("HZ_MEMBERS",        "hz1:5701,hz2:5701,hz3:5701")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{CONFIG_SERVER}/register",
                json={"name": "logging-service", "url": MY_URL},
                timeout=5.0,
            )
            print(f"[logging-service @ {MY_URL}] registered: {r.json()}", flush=True)
        except Exception as exc:
            print(f"[logging-service @ {MY_URL}] registration failed: {exc}", flush=True)
    yield


app = FastAPI(lifespan=lifespan)

hz_client = hazelcast.HazelcastClient(
    cluster_members=HZ_MEMBERS.split(","),
    cluster_name="dev",
)
distributed_map = hz_client.get_map("logs_map").blocking()


@app.post("/log")
async def log_transaction(data: dict = Body(...)):
    t_id = data.get("transaction_id")
    distributed_map.put(t_id, data)
    print(f"[logging-service @ {MY_URL}] stored transaction {t_id}", flush=True)
    return {"status": "ok"}


@app.get("/logs")
async def get_all_logs():
    return list(distributed_map.values())


@app.get("/logs/{user_id}")
async def get_user_logs(user_id: str):
    return [msg for msg in distributed_map.values()
            if str(msg.get("user_id")) == user_id]


if __name__ == "__main__":
    port = int(MY_URL.rsplit(":", 1)[-1])
    uvicorn.run(app, host="0.0.0.0", port=port)
