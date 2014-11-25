#!/bin/env python
# -*- coding: utf-8 -*-
"""
Parallel Module
~~~~~~~~~~~~~~

1. Dump computations in Amazon Queue.
2. Wait to receive all responses.
3. Compose a response

"""
from flask import Flask, Blueprint, jsonify
import json
import boto.sqs
from boto.sqs.message import Message
import string
import random
import os

# route prefix: /api/parallel
parallel = Blueprint('parallel',  __name__, static_folder = '../static')

# Connect to AWS region.
conn = boto.sqs.connect_to_region( os.environ['AWS_DEFAULT_REGION'] )
    
# Get the optima queue. We will error out if no queue is found. This is what is desired.
optima_queue = conn.get_queue( os.environ['AWS_WORKER_QUEUE'] )
optima_queue = optima_queue[0]

@parallel.route('/execute/<nprocesses>/<someparameter>', methods=['GET'])
def parallel_execution( nprocesses, someparameter ):

    # Expecting arguments to be integers
    nprocesses = int( nprocesses )
    someparameter = int ( someparameter )
    
    # A new queue to get response needs to be unique across all api calls
    response_queue_id = id_generator()
    q=conn.create_queue(response_queue_id)
        
    for i in range( nprocesses ):
        
        # Prepate a new message
        m = Message()
        m.set_body( json.dumps({'action': 'addition', 'iteration': i, 'parameter': someparameter, 'responseq': response_queue_id } ) )
        
        # Write to the queue
        optima_queue.write( m )
        
    result = []
    for i in range( nprocesses ):
        # We expect the process to complete in 3 minutes or less
        rs = q.get_messages(num_messages=1, wait_time_seconds=20)
        
        if ( len(rs) > 0 ):
            m = rs[0]
            resp = json.loads( m.get_body() )
            q.delete_message(m)
        
            result.append(resp['output'])
    
    # We are done, delete response q
    q.delete()
    
    # Return result as JSON
    return json.dumps( result )
    
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

