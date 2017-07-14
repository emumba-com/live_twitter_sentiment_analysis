"""
Module contains functions which launch threads for various purposes
"""
from threading import Thread
from kafka import KafkaConsumer
from tweet_ingestion import twitter
from semantic_analysis.Processor import Processor


def average_listener(topic, callback, connection, encoding):
    """
    monitors kafka for rolling average of sentiments and invokes the 
    callback when average is received
    :param topic: kafka topic to monitor
    :param callback: callback to invoke
    :param connection: kafka connection ip:port
    :param encoding: charset to decode average
    """
    print '---- average listener thread started ----'
    consumer = KafkaConsumer(topic, bootstrap_servers=[connection])
    print 'now listening to kafka on ', connection, ' against topic: ', topic
    for msg in consumer:
        print '-----new avg message received from kafka-----'
        message = msg.value.decode(encoding)
        print message
        callback(message)

def semantic_analyzer(source_topic, target_topic, connection, charset):
    """
    monitors kafka topic for tweets. On receiving tweets it calculates
    its sentiment and pushes the result onto another kafka topic
    :param source_topic: kafka topic which is source of tweets
    :param target_topic: kafka topic to put result
    :param connection: kafka connection ip:port
    :param charset: text encoding to decode tweet
    """
    print '---- sentiment analyzer thread started ----'
    processor = Processor(source_topic, target_topic, connection, charset)
    processor.start()


def tweet_fetcher(hashtag, topic, connection, encoding):
    """
    streams live tweets against a hashtag from twitter and puts
    them in kafka topic
    :param hashtag: twitter hashtag to stream
    :param topic: kafka topic to put tweets
    :param connection: kafka connection ip:port
    :param encoding: encoding for tweet
    """
    print '---- twitter ingestion thread started ----'
    twitter_client = twitter.TwitterClient(hashtag, topic, connection, encoding)
    twitter_client.start()


def launch(args, target):
    """
    launches a new thread
    :param args: arguments for thread function
    :param target: thread function
    """
    thread = Thread(target=target, args=args)
    thread.daemon = True
    thread.start()
