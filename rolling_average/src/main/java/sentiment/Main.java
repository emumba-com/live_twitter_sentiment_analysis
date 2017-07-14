package sentiment;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Properties;
import java.util.Set;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.function.VoidFunction;
import org.apache.spark.streaming.Duration;
import org.apache.spark.streaming.Durations;
import org.apache.spark.streaming.api.java.JavaDStream;
import org.apache.spark.streaming.api.java.JavaPairInputDStream;
import org.apache.spark.streaming.api.java.JavaStreamingContext;
import org.apache.spark.streaming.kafka.KafkaUtils;

import kafka.serializer.StringDecoder;
import scala.Tuple2;

/*
 * A separate program predicts sentiment of a Tweet and puts it in a Kafka topic.
 * 
 * This program launches a spark streaming server which monitors Kafka topic mentioned above
 * for incoming numbers. It then calculates average sentiment using a rolling window
 * approach 
 */
public class Main {

	static Producer<String, String> kafkaProducer;
	static String lastSumOfSentiments = null;
	public static final String KAFKA_CONNECTION_STRING = "localhost:9092";
	public static final String CHECKPOINTS_FOLDER = "/path_to_checkpoints_folder";
	public static final String KAFKA_TOPIC_TO_MONITOR = "sentiment";
	public static final String KAFKA_TOPIC_TO_SUBMIT_ROLLING_AVREGAE = "average";
	//length of window
	public static final int WINDOW_DURATION = 2;
	//how often to look
	public static final int SLIDE_DURATION = 2;
	
	public static void main(String[] args) throws Exception {

		Properties kafkaProducerProps = new Properties();
		kafkaProducerProps.put("bootstrap.servers", KAFKA_CONNECTION_STRING);
		kafkaProducerProps.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
		kafkaProducerProps.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
		kafkaProducer = new KafkaProducer<String, String>(kafkaProducerProps);
		
		SparkConf sparkConf = new SparkConf().setAppName("SentimentAverageByWindow");
		sparkConf.setMaster("local");

		JavaStreamingContext jssc = new JavaStreamingContext(sparkConf, Durations.seconds(1));
		jssc.checkpoint(CHECKPOINTS_FOLDER);
		jssc.sparkContext().setLogLevel("ERROR");

		Set<String> topics = new HashSet<>();
		topics.add(KAFKA_TOPIC_TO_MONITOR);
		Map<String, String> kafkaParams = new HashMap<String, String>();
		kafkaParams.put("metadata.broker.list", KAFKA_CONNECTION_STRING);

		// Create direct kafka stream with brokers and topics
		JavaPairInputDStream<String, String> messages = KafkaUtils.createDirectStream(
			jssc,
			String.class,
			String.class,
			StringDecoder.class,
			StringDecoder.class,
			kafkaParams, topics
		);

		JavaDStream<String> sentiments = messages.map(Tuple2::_2);
		Duration window = Durations.seconds(WINDOW_DURATION);
		Duration slide = Durations.seconds(SLIDE_DURATION);
		JavaDStream<String> reducedSentiment = sentiments
				.reduceByWindow((x, y) -> String.valueOf(Float.parseFloat(x) + Float.parseFloat(y)), window, slide);

		JavaDStream<Long> numberOfSentiments = sentiments.countByWindow(window, slide);

		VoidFunction<String> sentimentValueIterator = new VoidFunction<String>() {
			public void call(String sumOfSentimentValue) throws Exception {
				lastSumOfSentiments = sumOfSentimentValue;
			}
		};

		VoidFunction<JavaRDD<String>> sentimentRDDIterator = new VoidFunction<JavaRDD<String>>() {
			public void call(JavaRDD<String> rdd) throws Exception {
				rdd.foreach(sentimentValueIterator);
			}
		};

		VoidFunction<Long> countValueIterator = new VoidFunction<Long>() {
			public void call(Long countValue) throws Exception {
				if (countValue > 0 && lastSumOfSentiments != null) {
					//System.out.println("Count: " + s);
					//System.out.println("Sum: " + lastSumOfSentiment);
					sendToKafka(KAFKA_TOPIC_TO_SUBMIT_ROLLING_AVREGAE, Float.parseFloat(lastSumOfSentiments) / countValue);
				}
			}
		};

		VoidFunction<JavaRDD<Long>> countRDDIterator = new VoidFunction<JavaRDD<Long>>() {
			public void call(JavaRDD<Long> countRDD) throws Exception {
				countRDD.foreach(countValueIterator);
			}
		};

		// find sum of all sentiments within window
		reducedSentiment.foreachRDD(sentimentRDDIterator);
		// find number of all sentiments within window
		numberOfSentiments.foreachRDD(countRDDIterator);

		// Start the computation
		jssc.start();
		jssc.awaitTermination();
	}

	static void sendToKafka(String topic, Float average) {
		//System.out.println(average);
		kafkaProducer.send(new ProducerRecord<String, String>(topic, topic, String.valueOf(average)));
		//System.out.println("Message sent successfully");

	}
}
