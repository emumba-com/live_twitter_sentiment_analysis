"""
Module to do sentiment analysis on tweets
"""
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from nltk.sentiment.vader import SentimentIntensityAnalyzer

class Processor(object):
    """
    monitors kafka topic for tweets and performs sentiment analysis
    """
    kafka_producer = None
    kafka_consumer = None
    target_topic = None
    charset = None
    sid = SentimentIntensityAnalyzer()

    def __init__(self, source_topic, target_topic, kafka_connection, encoding):
        """
        to required initializations
        :param source_topic: kafka topic to fetch tweets from
        :param target_topic: kafka topic to put tweets
        :param kafka_connection: kafka connection string ip:port
        :param encoding: tweet decoder
        """
        self.kafka_producer = KafkaProducer(bootstrap_servers=kafka_connection)
        self.kafka_consumer = KafkaConsumer(source_topic, bootstrap_servers=[kafka_connection])
        self.charset = encoding
        self.target_topic = target_topic

    def start(self):
        """
        starts the sentiment analysis
        :rtype: object
        """
        for msg in self.kafka_consumer:
            print '-----new message for semantic analysis-----'
            message = msg.value.decode(self.charset)
            print message
            sentiment = self.sid.polarity_scores(message)
            print sentiment
            sentiment = sentiment['compound']
            sentiment = (sentiment + 1) / 2
            # print sentiment
            # producer = KafkaProducer(bootstrap_servers='localhost:9092')
            # producer.send(topic, message)
            # Asynchronous by default
            future = self.kafka_producer.send(self.target_topic, str(sentiment).encode(self.charset))
            # Block for 'synchronous' sends
            try:
                record_metadata = future.get(timeout=10)
            except KafkaError:
                pass

                # Successful result returns assigned partition and offset
                # print 'topic', (record_metadata.topic)
                # print 'partition', (record_metadata.partition)
                # print 'offset', (record_metadata.offset)
                # self.kafka_producer.put(self.target_topic, sentiment['compound'], self.charset)
