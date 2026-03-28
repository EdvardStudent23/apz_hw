import uvicorn
import hazelcast
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

# storage: Dict[str, dict] = {}
client = hazelcast.HazelcastClient(
    cluster_members=[
        "hz1:5701",
        "hz2:5701",
        "hz3:5701"
    ]
)

distributed_map = client.get_map("logs_map").blocking()


@app.post('/log')
async def log_transaction(data: dict = Body(...)):
    t_id = data.get("transaction_id")
    distributed_map.put(t_id, data)
    print(f"Logged transaction {t_id} in Hazelcast")
    return {"status": "ok"}


@app.get('/logs')
async def get_all_logs():
    return list(distributed_map.values())

@app.get('/logs/{user_id}')
async def get_msg(user_id: str):
    return [msg for msg in distributed_map.values() if str(msg.get("user_id") == user_id)]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
