import com.hazelcast.client.HazelcastClient;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.map.IMap;

public class MapTask {
    public static void main(String[] args) {
        HazelcastInstance client = HazelcastClient.newHazelcastClient(); // Підключення як клієнт [cite: 42]
        IMap<Integer, String> map = client.getMap("distributed-map"); // Створення Distributed Map [cite: 71, 72]

        for (int i = 0; i < 1000; i++) {
            map.put(i, "Value-" + i); // Запис 1000 значень [cite: 73]
        }

        System.out.println("Map filled with 1000 items.");
        client.shutdown();
    }
}