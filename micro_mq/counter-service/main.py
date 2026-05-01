import os, asyncio, uvicorn, httpx
import motor.motor_asyncio
import hazelcast
from fastapi import FastAPI
from contextlib import asynccontextmanager

CONFIG_SERVER = os.getenv("CONFIG_SERVER_URL", "http://config-server:9000")
MY_URL        = os.getenv("MY_URL",            "http://counter-service:8000")
HZ_MEMBERS    = os.getenv("HZ_MEMBERS",        "hz1:5701,hz2:5701,hz3:5701")
MONGO_URI     = os.getenv("MONGO_URI",         "mongodb://mongo_db:27017")

hz_client = hazelcast.HazelcastClient(
    cluster_members=HZ_MEMBERS.split(","),
    cluster_name="dev",
)
mq = hz_client.get_queue("transactions_queue").blocking()

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db           = mongo_client.bank_database
collection   = db.balances


async def _consume_loop():
    """Drain the Hazelcast queue and apply each transaction to MongoDB."""
    print("[counter-service] consumer loop started", flush=True)
    while True:
        try:
            item = await asyncio.to_thread(mq.poll, 2)
            if item is None:
                continue
            user_id = str(item.get("user_id"))
            amount  = int(item.get("amount", 0))
            doc = await collection.find_one_and_update(
                {"user_id": user_id},
                {"$inc": {"balance": amount}},
                upsert=True,
                return_document=True,
            )
            print(
                f"[counter-service] applied  user={user_id}  "
                f"amount={amount:+d}  new_balance={doc['balance']}",
                flush=True,
            )
        except asyncio.CancelledError:
            break
        except Exception as exc:
            print(f"[counter-service] consumer error: {exc}", flush=True)
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{CONFIG_SERVER}/register",
                json={"name": "counter-service", "url": MY_URL},
                timeout=5.0,
            )
            print(f"[counter-service] registered: {r.json()}", flush=True)
        except Exception as exc:
            print(f"[counter-service] registration failed: {exc}", flush=True)

    task = asyncio.create_task(_consume_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/balance/{user_id}")
async def get_user_balance(user_id: str):
    doc = await collection.find_one({"user_id": user_id})
    if doc:
        return {"balance": doc["balance"]}
    return {"balance": 0}


@app.get("/balances")
async def get_all_balances():
    balances = {}
    async for doc in collection.find({}):
        balances[doc["user_id"]] = doc["balance"]
    return balances


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
