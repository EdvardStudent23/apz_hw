#!/bin/sh
echo "=== Consul Init: Loading KV configurations ==="
sleep 3

ADDR="http://consul:8500"

# Hazelcast
consul kv put --http-addr=$ADDR config/hazelcast/members "hz1:5701,hz2:5701,hz3:5701"
consul kv put --http-addr=$ADDR config/hazelcast/cluster-name "dev"
consul kv put --http-addr=$ADDR config/hazelcast/map-name "logs_map"

# Message Queue
consul kv put --http-addr=$ADDR config/mq/members "hz1:5701,hz2:5701,hz3:5701"
consul kv put --http-addr=$ADDR config/mq/cluster-name "dev"
consul kv put --http-addr=$ADDR config/mq/queue-name "transactions_queue"
consul kv put --http-addr=$ADDR config/mq/poll-timeout-sec "2"

echo "=== KV load complete ==="
consul kv get --http-addr=$ADDR --recurse config/