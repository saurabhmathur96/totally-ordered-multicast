#!/usr/bin/env python3
import queue, time, random
import zmq

UNICAST = "UNICAST"
MULTICAST = "MULTICAST"
ACKNOWLEDGEMENT = "ACK"

class Node:
    def __init__(self, address, pub, sub, topic, peers):
        self.clock = 0
        self.address = address
        self.pub = pub
        self.sub = sub
        self.topic = topic
        self.peers = peers
        self.poller = zmq.Poller()
        self.poller.register(self.sub, zmq.POLLIN)
        self.receive_queue = queue.Queue()
        self.multicast_queue = queue.PriorityQueue()
        self.multicasts = {}


    def _send(self, topic, message_type, payload):
        self.clock += 1
        from_address = self.address
        payload = str(payload)
        message_id = to_id(from_address + payload)

        key = message_id
        if message_type == MULTICAST and message_id not in self.multicasts:
            self.multicasts[key] = { "message": [topic, from_address, self.clock, message_id, message_type, payload],
                                      "count": 0 }
            self.multicast_queue.put(((from_address, self.clock), key))

        message = "%s %s %s %s %s %s" % (topic, from_address, self.clock, message_id, message_type, payload)
        print ("[OUT] %s" % message)
        message = message.encode()
        self.pub.send(message)
    
    def _receive(self, block=False):
        kwargs = dict(flags=zmq.NOBLOCK) if not block else dict()
        message = self.sub.recv(**kwargs)
        message = message.decode()

        topic, from_address, clock, message_id, message_type, *rest = message.split(" ")
        print ("[IN] %s" % (message))
        clock = int(clock)
        self.clock = max(clock, self.clock) + 1
        return topic, from_address, clock, message_id, message_type, " ".join(rest)

    def send_unicast(self, address, payload):
        self._send(topic="%d" % to_id(address), message_type=UNICAST, payload=payload)
    

    def send_totally_ordered_multicast(self, payload):
        
        for address in self.peers:
            self._send(topic="%d" % to_id(address), message_type=MULTICAST, payload=payload)
    
    def _poll_for_messages(self, timeout=3000):
        events = dict(self.poller.poll(timeout))
        
        return events.get(self.sub) == zmq.POLLIN
    
    def check_for_messages(self):
        while self._poll_for_messages():
            
            topic, from_address, clock, message_id, message_type, payload = self._receive()
            clock = int(clock)
            message_id = int(message_id)
            message = [topic, from_address, clock, message_id, message_type, payload]
            key = message_id
                        
            if message_type == MULTICAST:
                if key not in self.multicasts: 
                    self.multicasts[key] = { "message": message,
                                             "count": 1 }

                    self.multicast_queue.put(((from_address, clock), key))
                    
                    # Send acknowledgements
                    for address in self.peers:
                        self._send(topic="%d" % to_id(address), message_type=ACKNOWLEDGEMENT, payload=message_id)
                else:
                    self.multicasts[key]["message"] = message
                    self.multicast_queue.put(((from_address, clock), key))
            

            if message_type == ACKNOWLEDGEMENT:
                key = int(payload)
                if key not in self.multicasts:
                    print ("key %s not found" % key) 
                    self.multicasts[key] = { "message": None,
                                             "count": 0 }
                

                self.multicasts[key]["count"] += 1

                

            elif message_type == UNICAST:
                self.receive_queue.put(message)

        
        while not self.multicast_queue.empty():
            priority, message_id = self.multicast_queue.get()

            if self.multicasts[message_id]["count"] != len(self.peers):
                self.multicast_queue.put((priority, message_id))
                break
            
            item = self.multicasts.pop(message_id)
            self.receive_queue.put(item["message"])


        
        
          

    def has_messages(self):
        return not self.receive_queue.empty()
    
    def receive(self):
        item = self.receive_queue.get()
        topic, from_address, clock, message_id, message_type, payload = item
        return topic, from_address, clock, message_id, message_type, payload



def to_id(address):
    return sum(ord(c) for c in address) % (10 ** 8)

def start_node(port, addresses, topic):
    context = zmq.Context()

    pub = context.socket(zmq.PUB)
    bind_address = "tcp://*:%s" % port
    
    pub.bind(bind_address)

    print ("Binding to %s" % bind_address)

    sub = context.socket(zmq.SUB)
    for address in addresses:
        sub.connect(address)
    
    receive_address = "tcp://localhost:%d" % port
    sub.setsockopt(zmq.SUBSCRIBE, b"%d" % to_id(receive_address)) # unicast
    sub.setsockopt(zmq.SUBSCRIBE, b"%d" % topic) # multicast

    print ("Subscribed to %d for unicast" % to_id(receive_address))
    print ("Subscribed to %s for multicast" % topic)
        
        

    node = Node(address=receive_address, pub=pub, sub=sub, topic=topic, peers=addresses)
    time.sleep(1)
    return node


