import asyncio
import httpx
import time

FACADE_URL = "http://localhost:8000"

async def run_client(client_id, num_requests, same_account=False):
    async with httpx.AsyncClient(timeout=None) as client:
        user_id = "target_user" if same_account else f"user_{client_id}"
        for _ in range(num_requests):
            try:
                await client.post(
                    f"{FACADE_URL}/process",
                    json={"user_id": user_id, "amount": 1}
                )
            except Exception:
                pass

async def get_stats():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{FACADE_URL}/stats")
        data = res.json()
        return data.get("logging", 0), data.get("counter_enqueue", 0)

async def run_test(num_clients, req_per_client, same_account):
    label = "Same account: True" if same_account else "Same account: False"
    print(f"\nStarting Test: {num_clients} clients, {req_per_client} reqs each ({label})")

    initial_log, initial_cnt = await get_stats()
    start_time = time.time()

    tasks = [run_client(i, req_per_client, same_account) for i in range(num_clients)]
    await asyncio.gather(*tasks)

    end_time = time.time()
    final_log, final_cnt = await get_stats()

    total_time = end_time - start_time
    total_reqs = num_clients * req_per_client
    log_time = final_log - initial_log
    cnt_time = final_cnt - initial_cnt

    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests Per Second: {total_reqs / total_time:.2f}")
    print(f"Logging Overhead: {log_time:.2f}s ({(log_time/total_time)*100:.1f}%)")
    print(f"Counter Overhead: {cnt_time:.2f}s ({(cnt_time/total_time)*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(run_test(10, 10000, same_account=False))
    asyncio.run(run_test(10, 10000, same_account=True))