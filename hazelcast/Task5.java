import com.hazelcast.client.HazelcastClient;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.map.IMap;

public class Task5 {
    public static void main(String[] args) {
        HazelcastInstance client = HazelcastClient.newHazelcastClient();
        IMap<String, Integer> map = client.getMap("task5-pessimistic");
        map.putIfAbsent("key", 0);

        System.out.println("Starting pessimistic lock increment...");
        long startTime = System.currentTimeMillis();

        for (int k = 0; k < 10_000; k++) {
            map.lock("key");
            try {
                Integer value = map.get("key");
                value++;
                map.put("key", value);
            } finally {
                map.unlock("key");
            }
        }

        long endTime = System.currentTimeMillis();
        System.out.println("Finished in " + (endTime - startTime) + " ms.");
        System.out.println("Final value: " + map.get("key"));
        client.shutdown();
    }
}