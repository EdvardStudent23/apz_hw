import time, uuid, httpx
from fastapi import FastAPI, Body


app = FastAPI()

metrics = {"logging": 0.0, "counter": 0.0}

LOG_URL = "http://logging-service:8000"
CNT_URL = "http://counter-service:8000"

@app.post("/process")
async def handle_post(data: dict = Body(...)):
    t_id = str(uuid.uuid4())
    payload = {**data, "transaction_id": t_id}

    async with httpx.AsyncClient() as client:
        start_log = time.time()
        await client.post(f"{LOG_URL}/log", json=payload)
        metrics['logging'] += (time.time() - start_log)

        start_count = time.time()
        res = await client.post(f'{CNT_URL}/transaction', json=payload)
        metrics['counter'] += (time.time() - start_count)

    return {'transaction_id': t_id, 'balance': res.json()["balance"]}

@app.get("/user/{user_id}")
async def get_user(user_id: str):
    async with httpx.AsyncClient() as client:
        b = await client.get(f'{CNT_URL}/balance/{user_id}')
        t = await client.get(f'{LOG_URL}/logs/{user_id}')

    return {'balance': b.json()['balance'], 'transactions': t.json()}

@app.get("/accounts")
async def get_accounts():
    async with httpx.AsyncClient() as client:
        res = await client.get(f'{CNT_URL}/balances')
    
    return res.json()

@app.get('/stats')
async def get_stats():
    return metrics

