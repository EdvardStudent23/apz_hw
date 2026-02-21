import uvicorn
from fastapi import FastAPI, Body
from typing import Dict

app = FastAPI()

balances: Dict[str, int] = {}

@app.post('/transaction')
async def process_transaction(data: dict = Body(...)):
    user_id = str(data.get('user_id'))
    amount = int(data.get("amount"))

    current_balance = balances.get(user_id, 0)
    balances[user_id] = current_balance + amount

    return {'balance': balances[user_id]}

@app.get('/balance/{user_id}')
async def get_user_balance():
    return {'balance': balances.get(user_id, 0)}

@app.get('/balances')
async def get_all_balances():
    return balances
