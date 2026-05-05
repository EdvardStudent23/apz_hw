"""
counter-service/main.py
"""
import os, asyncio, logging, uvicorn, hazelcast
import motor.motor_asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from consul_helper import kv_get, register_service, deregister_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MY_URL       = os.getenv("MY_URL",       "http://counter-service-1:8000")
SERVICE_NAME = os.getenv("SERVICE_NAME", "counter-service")
MONGO_URI    = os.getenv("MONGO_URI",    "mongodb://mongo_db:27017")

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
collection   = mongo_client.bank_database.balances

hz_client = None
mq        = None
_poll_sec = 2.0

async def _consume_loop():
    logger.info(f"[{SERVICE_NAME} @ {MY_URL}] consumer loop started")
    while True:
        try:
            item = await asyncio.to_thread(mq.poll, _poll_sec)
            if item is None:
                continue
            user_id = str(item.get("user_id"))
            amount  = int(item.get("amount", 0))
            doc = await collection.find_one_and_update(
                {"user_id": user_id},
                {"$inc": {"balance": amount}},
                upsert=True, return_document=True,
            )
            logger.info(f"[{SERVICE_NAME} @ {MY_URL}] user={user_id} amount={amount:+d} balance={doc['balance']}")
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(f"[{SERVICE_NAME}] consumer error: {exc}")
            await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global hz_client, mq, _poll_sec

    # Вимога 1 — реєстрація
    register_service(name=SERVICE_NAME, my_url=MY_URL, health_path="/health")
    logger.info(f"[{SERVICE_NAME} @ {MY_URL}] registered in Consul")

    # Вимога 4 — MQ конфіг з Consul KV
    mq_members    = kv_get("config/mq/members",          "hz1:5701,hz2:5701,hz3:5701")
    mq_cluster    = kv_get("config/mq/cluster-name",     "dev")
    mq_queue_name = kv_get("config/mq/queue-name",       "transactions_queue")
    _poll_sec     = float(kv_get("config/mq/poll-timeout-sec", "2"))
    logger.info(f"[{SERVICE_NAME}] KV → queue={mq_queue_name!r} cluster={mq_cluster!r} poll={_poll_sec}s")

    hz_client = hazelcast.HazelcastClient(cluster_members=mq_members.split(","), cluster_name=mq_cluster)
    mq        = hz_client.get_queue(mq_queue_name).blocking()
    logger.info(f"[{SERVICE_NAME}] Hazelcast MQ ready")

    task = asyncio.create_task(_consume_loop())
    yield

    task.cancel()
    deregister_service()
    hz_client.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok", "service": SERVICE_NAME, "instance": MY_URL}

@app.get("/balance/{user_id}")
async def get_balance(user_id: str):
    doc = await collection.find_one({"user_id": user_id})
    return {"balance": doc["balance"] if doc else 0}

@app.get("/balances")
async def get_all_balances():
    balances = {}
    async for doc in collection.find({}):
        balances[doc["user_id"]] = doc["balance"]
    return balances

if __name__ == "__main__":
    port = int(MY_URL.rsplit(":", 1)[-1])
    uvicorn.run(app, host="0.0.0.0", port=port)
