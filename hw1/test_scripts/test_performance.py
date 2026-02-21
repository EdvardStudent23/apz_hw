import asyncio
import httpx
import time

FACADE_URL = "http://localhost:8080/process"

async def run_client(client_id, num_requests, same_account=False):
    async with httpx.AsyncClient() as client:
        user_id = "target_user" if same_account else f"user_{client_id}"

        for _ in range(num_requests):
            await client.post(FACADE_URL, json={"user_id": user_id, "amount": 1})

async def run_test(num_clients, req_per_client, same_account):
    print(f"Starting Test: {num_clients} clients, {req_per_client} reqs each...")
    start_time = time.time()

    tasks = [run_client(i, req_per_client, same_account) for i in range(num_clients)]
    await asyncio.gather(*tasks)

    end_time = time.time()
    total_time = end_time - start_time
    total_reqs = num_clients * req_per_client

    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests Per Second: {total_reqs / total_time:.2f}")

if __name__ == "__main__":
    #scenario 10 clients, 10k each, different accounts
    asyncio.run(run_test(10, 10000, same_account=False))

    #scenario 2: 10 clients, 10k each, same account
    asyncio.run(run_test(10, 10000, same_account=True))