import time, uuid, httpx, random
from fastapi import FastAPI, Body, HTTPException

app = FastAPI()

metrics = {"logging": 0.0, "counter": 0.0}

LOG_URLS = [
    "http://logging-1:8000",
    "http://logging-2:8000",
    "http://logging-3:8000"
]
CNT_URL = "http://counter-service:8000"

@app.post("/process")
async def handle_post(data: dict = Body(...)):
    t_id = str(uuid.uuid4())
    payload = {**data, "transaction_id": t_id}

    available_nodes = list(LOG_URLS)
    random.shuffle(available_nodes)

    async with httpx.AsyncClient() as client:
        logged_successfully = False
        start_log = time.time()
        
        for node_url in available_nodes:
            try:
                await client.post(f"{node_url}/log", json=payload, timeout=2.0)
                logged_successfully = True
                break
            except httpx.RequestError:
                continue
                
        metrics['logging'] += (time.time() - start_log)

        if not logged_successfully:
            raise HTTPException(status_code=500, detail="All logging services are down")

        start_count = time.time()
        res = await client.post(f'{CNT_URL}/transaction', json=payload)
        metrics['counter'] += (time.time() - start_count)

    return {'transaction_id': t_id, 'balance': res.json()["balance"]}

@app.get("/user/{user_id}")
async def get_user(user_id: str):
    random_log_url = random.choice(LOG_URLS)
    
    async with httpx.AsyncClient() as client:
        b = await client.get(f'{CNT_URL}/balance/{user_id}')
        t = await client.get(f'{random_log_url}/logs/{user_id}')

    return {'balance': b.json()['balance'], 'transactions': t.json()}

@app.get("/accounts")
async def get_accounts():
    async with httpx.AsyncClient() as client:
        res = await client.get(f'{CNT_URL}/balances')
    return res.json()

@app.get('/stats')
async def get_stats():
    return metrics