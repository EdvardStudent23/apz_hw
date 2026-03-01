import hazelcast
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger("hazelcast").setLevel(logging.WARNING)

CLUSTER_NAME = "dev"
CLUSTER_MEMBERS = ["127.0.0.1:5701", "127.0.0.1:5702", "127.0.0.1:5703"]

def get_client():
    return hazelcast.HazelcastClient(
        cluster_name=CLUSTER_NAME,
        cluster_members=CLUSTER_MEMBERS
    )

ITERATIONS = 10000
KEY = "my-key"