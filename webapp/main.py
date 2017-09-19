"""
This program lanuches a flask based web server and 3 threads

(1)ingests stream of tweets from twitter against a particular hashtag
and puts them in a kafka topic

(2)monitors kafka topic for tweets, calculates sentiments and put it
in another kafka topic

* a seprate java program reads sentiments from kafka topic, calculates
rolling mean and puts it in another kafka topic

(3)monitors kafka topic for sentiment average and invokes given callback

Average sentiments are sent to clients in real time via socketio
"""

# monkey patching, read details in link below
# https://github.com/miguelgrinberg/Flask-SocketIO/issues/418
import eventlet
eventlet.monkey_patch()

import socketio
from flask import Flask, current_app
import threads

KAFKA_TOPIC_FOR_AVERAGE = 'average'
KAFKA_TOPIC_FOR_SENTIMENT = 'sentiment'
KAFKA_TOPIC_FOR_TWEETS = 'tweet'
KAFKA_CONNECTION_STRING = 'localhost:9092'
TWEET_ENCODING = 'utf-8'
TWITTER_HASHTAG = 'happy'

sio = socketio.Server()
app = Flask(__name__)


@app.route('/<path:path>')
def index(path):
    """
    servers client web requests
    :param path: request path
    :return: requested resource
    """
    print 'request on server: ', path
    return current_app.send_static_file(path)


@sio.on('connect')
def connect(sid, environment):
    """
    method gets called when a new client connects with server
    via socket io
    :param sid: socket id
    :param environment:
    """
    print 'connected: ', sid


@sio.on('disconnect')
def disconnect(sid):
    """
    methods is called when a socket io connection disconnects
    :param sid: sid of disconnected socket
    """
    print 'client disconnected: ', sid


def average_callback(average):
    """
    method is called whenever rolling average sentiment is received
    from java program via kafka.
    :param average: average sentiment
    """
    # send this average to all connected clients
    sio.emit('event', average)


if __name__ == '__main__':
    # launch thread to capture rolling average of sentiment
    threads.launch(
        (
            KAFKA_TOPIC_FOR_AVERAGE,
            average_callback,
            KAFKA_CONNECTION_STRING,
            TWEET_ENCODING
        ),
        threads.average_listener
    )

    # launch thread to do sentiment analysis on tweets
    threads.launch(
        (
            KAFKA_TOPIC_FOR_TWEETS,
            KAFKA_TOPIC_FOR_SENTIMENT,
            KAFKA_CONNECTION_STRING,
            TWEET_ENCODING
        ), 
        threads.semantic_analyzer
    )

    # lanuch thread to stream tweets from twitter
    threads.launch(
        (
            TWITTER_HASHTAG,
            KAFKA_TOPIC_FOR_TWEETS,
            KAFKA_CONNECTION_STRING,
            TWEET_ENCODING
        ),
        threads.tweet_fetcher
    )

    app = socketio.Middleware(sio, app)
    print 'server started on port 8001'
    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('', 8001)), app)
