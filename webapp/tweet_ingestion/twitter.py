"""
Contains classes which stream tweets live from twitter and put them
in kafka topic
"""
import tweepy
from kafka.errors import KafkaError
from kafka import KafkaProducer
from tweet_ingestion import config

class TwitterClient(object):
    """
    Twitter client to download live stream of tweets
    from twitter against a particular hashtag
    """
    api = None
    tweet_stream = None
    hashtag = None
    topic = None
    kafka_producer = None
    encoding = None

    def __init__(self, hashtag, topic, connection, encoding):
        """
        init various objects required later
        :param hashtag: twitter hashtag to monitor
        :param topic: kafka topic to put tweets into
        :param connection: kafka connection string ip:port
        :param encoding: charset to encode tweets
        """
        self.topic = topic
        self.hashtag = hashtag
        auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)
        self.api = tweepy.API(auth)
        self.kafka_producer = KafkaProducer(bootstrap_servers=connection)
        self.encoding = encoding

    def start(self):
        """
        starts streaming tweets
        """
        tweet_listener = TweetListener(self.tweet_callback)
        tweet_stream = tweepy.Stream(auth=self.api.auth, listener=tweet_listener)
        tweet_stream.filter(languages=["en"], track=[self.hashtag])

    def tweet_callback(self, tweet):
        """
        method is called when a tweet is received from twitter.
        it puts the tweet on kafka topic
        :param tweet:
        """
        print 'sending to kafka on topic: ', self.topic
        future = self.kafka_producer.send(self.topic, tweet.encode(self.encoding))
        # Block for 'synchronous' sends
        try:
            record_metadata = future.get(timeout=10)
        except KafkaError:
            pass
        # Successful result returns assigned partition and offset
        print 'topic', (record_metadata.topic)
        print 'partition', (record_metadata.partition)
        print 'offset', (record_metadata.offset)

    def stop(self):
        """
        stops the streaming
        """
        if self.tweet_stream != None:
            self.tweet_stream.disconnect()


class TweetListener(tweepy.StreamListener):
    """
    Class to listen for tweets from twitter
    """
    tweet_callback = None

    def __init__(self, callback):
        """
        init required variables
        :param callback: method to invoke when a tweet is received
        """
        super(TweetListener, self).__init__()
        self.tweet_callback = callback

    def on_status(self, status):
        """
        this method is called on receving a new tweet
        :param status: tweet object
        """
        print '------- new tweet from twitter---------'
        print status.text
        self.tweet_callback(status.text)

    def on_error(self, status_code):
        """
        method for error handling
        :param status_code: error status code
        :return: False to quit
        """
        print '------- streaming error ---------'
        print 'Error occured: ,', status_code
        if status_code == 420:
            # returning False in on_data disconnects the stream
            return False
