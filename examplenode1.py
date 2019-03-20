#!/usr/bin/env python3

from node import start_node, to_id
import argparse, time, random, pprint, sys

parser = argparse.ArgumentParser()
parser.add_argument("port", type=int, help="port id")
parser.add_argument("topic", type=int, help="topic id for a group of nodes")
parser.add_argument("addresses", nargs="+", help="addresses of other nodes in group")
args = parser.parse_args()


node = start_node(args.port, args.addresses, args.topic)
time.sleep(2)


i = 0
id = to_id("tcp://localhost:%d" % args.port)

multicasts = []
while True:
    
    if i < 5:
        i += 1
        coin = random.randint(0, 1) 
        if coin == 0:
            node.send_totally_ordered_multicast("message(MULTICAST, %d, %d)" % (id, i))
        else:
            node.send_unicast(args.addresses[random.randint(0, len(args.addresses)-1)], "message(UNICAST, %d, %d)" % (id, i))
    else:
        for address in args.addresses:
            node.send_unicast(address, "EXIT")

    node.check_for_messages()
    while node.has_messages():
        message = node.receive()
        message = message[-1]
        
        if "MULTICAST" in message:
            multicasts.append(message)
        print (message + "<- Message received by application ")
        if message == "EXIT":
            pprint.pprint(multicasts)
            exit()

    sys.stdout.flush()
    time.sleep(1)