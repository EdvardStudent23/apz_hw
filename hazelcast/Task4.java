import com.hazelcast.client.HazelcastClient;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.map.IMap;

public class Task4 {
    public static void main(String[] args) {
        HazelcastInstance client = HazelcastClient.newHazelcastClient();
        IMap<String, Integer> map = client.getMap("task4");

        map.putIfAbsent("key", 0);

        System.out.println("incrementation cycle 10 000");

        long startTime = System.currentTimeMillis();
        for (int k = 0; k < 10_000; k++) {
            Integer value = map.get("key"); 
            value++; // 
            map.put("key", value); 
        }
        long endTime = System.currentTimeMillis();

        System.out.println("Finished in " + (endTime - startTime) + " ms.");
        System.out.println("The current key value " + map.get("key"));
        
        client.shutdown();
    }
}