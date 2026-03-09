import com.hazelcast.client.HazelcastClient;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.collection.IQueue;

public class Task8QueueConsumer {
    public static void main(String[] args) throws Exception {
        HazelcastInstance client = HazelcastClient.newHazelcastClient();
        IQueue<Integer> queue = client.getQueue("bounded-queue");

        while (true) {
            Integer item = queue.take();
            System.out.println("Consumed: " + item);
            Thread.sleep(100); 
        }
    }
}