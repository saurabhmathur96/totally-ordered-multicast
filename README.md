# Totally Ordered Multicast

The messaging functionality is implemented on top of ZeroMQ Pub-Sub sockets.
The implementation was written in Python 3.5.3 on a Debian Linux Machine using the pyzmq package.

## Implementation details
Each message is a string for the following format:
```topic from_address clock message_id message_type payload```
Where 
- `topic` is the pub-sub topic shared among all nodes.
- `from_address` is the address of the sender process.
- `clock` is the lamport timestamp (int) of the sender process.
- `message_id` is a unique id assigned to each message. It is computed by applying a hash function to `from_address+payload`
- `message_type` can `UNICAST`, `MULTICAST` or `ACK`
- `payload` the actual content of the message

`node.py` contains the implmentation for a process node. It has two methods to send messages:
- `send_unicast(address, payload)` sends a single unordered message to a specific node.
- `send_totally_ordered_multicast(payload)` sends a totally ordered multicast to all peers.


The `check_for_messages` method must be called periodically to transfer received and ready messages to the `receive_queue`
When a unicast is received, it is added to the `receive_queue` immediately.
When a totally ordered multicast is received, it is added to the `multicasts` dictionary which maps the `message_id` to `count` and the `message`. It is also added to a priority queue called `multicast_queue` which is ordered by (`sender_id`, `sender_timestamp`).
Then the acknowledgement count of the head of the queue is inspected. If all acknowlegements have been received, then that message is removed from the `multicasts` dictionary and from the `multicast_queue` and it is pushed to the `receive_queue`.


The `receive` method pops a message from the `receive_queue` and returns it.


Instead of sending the multicast to the sender node, it is assumed to be received immediately and the `receive_queue` and `multicasts` dictionary are updated.

## Testing
`test.sh` is Test Script. It spawns three processes that exchange messages using the following algorithm.

```
i = 0
i = i + 1
If i < 5 then,
    Flip a coin.
    If heads, send a Totally Ordered Multicast with payload i.
    If tails, send a Unicast to a random peer with payload i
else,
    Send a Unicast ot all peers with payload EXIT
Check for messages
If there are any messages, receive them and print their content.
If received message is EXIT,
    print all received multicasts in the order
    exit
```

The output can be seen in the log files 4000.log.txt, 5000.log.txt, 6000.log.txt.

Since the test-algorithm is stochastic, multiple runs will have different test-patterns - effectively giving a total 6^5 = 7,776 possible unique test-cases. 


## Assumptions
The only assumption that I make here is that a multicast will be sent to all peers in a group. However, a multicast to specific addresses can be achieved by creating a new object of Node class for those processes. 
The addresses of the peers of the sub-group could also have been sent with the message as a header.