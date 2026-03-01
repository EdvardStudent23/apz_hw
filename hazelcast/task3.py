import hazelcast

client = hazelcast.HazelcastClient(
    cluster_name="dev",
    cluster_members=["127.0.0.1:5701", "127.0.0.1:5702", "127.0.0.1:5703"]
)

capitals_map = client.get_map("capitals")
futures = []

print("start writing 1000")

for i in range(1000):
    future = capitals_map.set(i, f"City-{i}")
    futures.append(future)

for future in futures:
    future.result()

print(f"Writing is finished. the size {capitals_map.blocking().size()}")
client.shutdown()