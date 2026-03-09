import com.hazelcast.client.HazelcastClient;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.map.IMap;

public class Task6 {
    public static void main(String[] args) {
        HazelcastInstance client = HazelcastClient.newHazelcastClient();
        IMap<String, Integer> map = client.getMap("task6-optimistic");
        map.putIfAbsent("key", 0);

        System.out.println("Starting optimistic lock increment...");
        long startTime = System.currentTimeMillis();

        for (int k = 0; k < 10_000; k++) {
            while (true) {
                Integer oldValue = map.get("key");
                Integer newValue = oldValue + 1;
                if (map.replace("key", oldValue, newValue)) {
                    break;
                }
            }
        }

        long endTime = System.currentTimeMillis();
        System.out.println("Finished in " + (endTime - startTime) + " ms.");
        System.out.println("Final value: " + map.get("key"));
        client.shutdown();
    }
}