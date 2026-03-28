import asyncio
import httpx
import time

FACADE_URL = "http://localhost:8000"

async def run_client(client_id, num_requests, same_account=False):
    async with httpx.AsyncClient(timeout=None) as client:
        user_id = "target_user" if same_account else f"user_{client_id}"
        for _ in range(num_requests):
            try:
                await client.post(f"{FACADE_URL}/process", json={"user_id": user_id, "amount": 1})
            except Exception:
                pass

async def get_stats():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{FACADE_URL}/stats")
        return res.json()

async def run_test(num_clients, req_per_client, same_account):
    print(f"\nStarting Test: {num_clients} clients, {req_per_client} reqs each (Same account: {same_account})")
    initial_stats = await get_stats()
    start_time = time.time()

    tasks = [run_client(i, req_per_client, same_account) for i in range(num_clients)]
    await asyncio.gather(*tasks)

    end_time = time.time()
    final_stats = await get_stats()

    total_time = end_time - start_time
    total_reqs = num_clients * req_per_client

    log_time = final_stats['logging'] - initial_stats['logging']
    count_time = final_stats['counter'] - initial_stats['counter']

    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests Per Second: {total_reqs / total_time:.2f}")
    print(f"Contribution - Logging: {log_time:.2f}s ({(log_time/total_time)*100:.1f}%)")
    print(f"Contribution - Counter: {count_time:.2f}s ({(count_time/total_time)*100:.1f}%)")

if __name__ == "__main__":
    
    asyncio.run(run_test(10, 10000, same_account=False))
    asyncio.run(run_test(10, 10000, same_account=True))