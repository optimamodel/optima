import flask
from flask import request, Response
import boto.sqs
from boto.sqs.message import Message

import boto

# Create and configure the Flask app
application = flask.Flask(__name__)
application.debug = True

# Connect to AWS region.
conn = boto.sqs.connect_to_region(
    "us-east-1" )

@application.route('/', methods=['POST'])
def optima_compute():

    response = None
    if request.json is None:
        # Expect application/json request
        response = Response("", status=415)
    else:
        message = dict()
        try:
            # Action to be performed
            action = request.json['action']
            
            # Queue to send response back to
            queue = request.json['responseq']
            
            # Check action to determine processing. We just have one command now
            output = runprocess( request.json )
            
            # Get the response queue
            rs_queue = conn.get_queue( queue )
    
            m = Message()
            m.set_body( json.dumps({ 'output': output } ) )
    
            # Write the response
            rs_queue.write( m )
            
            response = Response("", status=200)
        except Exception as ex:
            logging.exception('Error processing message: %s' % request.json)
            response = Response(ex.message, status=500)

    return response

 
def runprocess( req ):    
    i = req['iteration']
    someparameter = req['parameter']
    output = someparameter+i*2
    return output


if __name__ == '__main__':
    application.run(host='0.0.0.0')