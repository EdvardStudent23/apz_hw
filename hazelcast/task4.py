import hazelcast
import time

client = hazelcast.HazelcastClient(
    cluster_name="dev",
    cluster_members=["127.0.0.1:5701", "127.0.0.1:5702", "127.0.0.1:5703"]
)

hz_map = client.get_map("no_lock_map")
hz_map.put_if_absent("key", 0).result()

print("Starting 10,000 increments...")
start_time = time.time()

for _ in range(10000):
    value = hz_map.get("key").result() or 0
    hz_map.put("key", value + 1).result()

end_time = time.time()
final_value = hz_map.get("key").result()

print(f"Time: {end_time - start_time:.2f} s")
print(f"Final value: {final_value}")

client.shutdown()