import uvicorn
import motor.motor_asyncio
from fastapi import FastAPI, Body
from typing import Dict

app = FastAPI()

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongo_db:27017")
db = client.bank_database
collection = db.balances


@app.post('/transaction')
async def process_transaction(data: dict = Body(...)):
    user_id = str(data.get('user_id'))
    amount = int(data.get("amount"))

    # Оновлюємо баланс у БД (якщо юзера нема - створюємо)
    document = await collection.find_one_and_update(
        {"user_id": user_id},
        {"$inc": {"balance": amount}},
        upsert=True,
        return_document=True
    )
    
    return {'balance': document['balance']}

@app.get('/balance/{user_id}')
async def get_user_balance(user_id: str):
    document = await collection.find_one({"user_id": user_id})
    if document:
        return {'balance': document['balance']}
    return {'balance': 0}

@app.get('/balances')
async def get_all_balances():
    cursor = collection.find({})
    balances = {}
    async for doc in cursor:
        balances[doc['user_id']] = doc['balance']
    return balances

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)