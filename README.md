This project does sentiment analysis of tweets associated with a particular twitter hashtag, in real time, in an scalable manner, and visualizes it using spark-line plot.

export SPARK_HOME="/Users/haris/Documents/Office/spark-2.1.1-bin-hadoop2.7"
export PYTHONPATH=$SPARK_HOME/python
sh zookeeper-server-start.sh ../config/zookeeper.properties
sh kafka-server-start.sh ../config/server.properties
start ingestion
start sentiment
start avg calculation
