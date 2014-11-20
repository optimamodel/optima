from flask.ext.script import Manager
from flask import Flask
import os
import boto.sqs
from boto.sqs.message import Message
import time
import requests
import json

app = Flask(__name__)
manager = Manager(app)

@manager.command
def loop():
    
    print "Setting up connection to AWS..."
    
    # Connect to AWS region.
    conn = boto.sqs.connect_to_region( os.environ['AWS_DEFAULT_REGION'] )
    
    print "Getting queue..."
    
    # Get the optima queue. We will error out if no queue is found. This is what is desired.
    optima_queue = conn.get_all_queues( os.environ['AWS_WORKER_QUEUE_PREFIX'] )
    optima_queue = optima_queue[0]
    
    print "Going in a loop reading queue"
    
    while True:
        try:
            # Get messages from queue
            rs = optima_queue.get_messages( 10, wait_time_seconds=20)
            
            # Process one message at a time
            for m in rs:
                
                print "Processing a message"
                print m.get_body()
                
                # Make a post request
                r = requests.post('http://localhost:5001/', json=m.get_body())
                
                # Done processing, delete message
                optima_queue.delete_message(m)
                
            
        except Exception as ex:
            print ex.message
            
        time.sleep(1)
        

if __name__ == "__main__":
    manager.run()