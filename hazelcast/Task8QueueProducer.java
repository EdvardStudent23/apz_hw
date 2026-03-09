import com.hazelcast.client.HazelcastClient;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.collection.IQueue;

public class Task8QueueProducer {
    public static void main(String[] args) throws Exception {
        HazelcastInstance client = HazelcastClient.newHazelcastClient();
        IQueue<Integer> queue = client.getQueue("bounded-queue");

        for (int i = 1; i <= 100; i++) {
            System.out.println("Producing: " + i);
            queue.put(i); 
        }
        
        System.out.println("Producer Finished!");
        client.shutdown();
    }
}