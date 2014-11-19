import flask
from flask import request, Response
import boto.sqs
from boto.sqs.message import Message
import json
import boto
import logging
from logging.handlers import RotatingFileHandler

import os

# Create and configure the Flask app
application = flask.Flask(__name__)
application.debug = True

handler = RotatingFileHandler('optima-worker.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
application.logger.handlers = []
application.logger.addHandler(handler)

application.logger.info("Worker setting up...")

# Connect to AWS region.
region = os.environ.get('AWS_DEFAULT_REGION')
if region is None:
    region = "us-west-2"

conn = boto.sqs.connect_to_region( region )

@application.route('/execute', methods=['POST'])
def optima_compute():
    application.logger.info("Inside the request")
    application.logger.info(request.get_json( force=True ))
    try:
        application.logger.info(request.json)
    except Exception as ex:
        application.logger.error('Error processing message: %s' % request.json)
    
    response = None
    if request.json is None:
        # Expect application/json request
        response = Response("", status=415)
    else:
        try:
            
            js = json.loads(request.json)
            
            application.logger.info('Begin json analysis')
            
            # Action to be performed
            action = js['action']
            
            # Queue to send response back to
            queue = js['responseq']
            
            application.logger.info('Begin message processing')
            
            # Check action to determine processing. We just have one command now
            output = runprocess( js )
            
            application.logger.info('Get the response queue')
            
            # Get the response queue
            rs_queue = conn.get_queue( queue )
    
            m = Message()
            m.set_body( json.dumps({ 'output': output } ) )
    
            application.logger.info('Write to response queue')
    
            # Write the response
            rs_queue.write( m )
            
            application.logger.info('We are done!')
            
            response = Response("", status=200)
        except Exception as ex:
            application.logger.error('Error processing message: %s' % request.json)
            response = Response(ex.message, status=500)

    return response

@application.route('/info', methods=['GET'])
def info():
    return Response("Optima Worker v.1.0.0", status=200)
 
def runprocess( req ):    
    i = req['iteration']
    someparameter = req['parameter']
    output = someparameter+i*2
    return output

application.logger.info("Worker setup complete")

if __name__ == '__main__':
    port = int(os.environ.get('AWS_WORKER_PORT'))
    
    if port is None:
        port = 5000
    
    application.run(host='0.0.0.0', port=port)