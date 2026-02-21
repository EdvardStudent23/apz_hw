import uvicorn
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

storage: Dict[str, dict] = {}

class TransactionMessage(BaseModel):
    uuid: str
    msg: str

@app.post('/log')
async def log_transaction(data: dict = Body(...)):
    t_id = data.get("transaction_id")
    storage[t_id] = data
    print(f"Logged: {t_id}")
    return {"status":"ok"}


@app.get('/logs')
async def get_all_logs():
    return list(storage.values())

@app.get('/logs/{user_id}')
async def get_msg(user_id: str):
    return [msg for msg in storage.values() if str(msg.get("user_id") == user_id)]

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
