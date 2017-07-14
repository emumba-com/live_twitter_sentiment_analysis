# Twitter sentiment analysis in real-time
This project implements a scalable architecture to monitor and visualize sentiment against a twitter hashtag in real-time.

### System design
![system design](https://user-images.githubusercontent.com/1760859/28226668-6bc5ce04-68f0-11e7-864f-529340a08d59.png)

### Project breakdown
Project has two parts

#### 1. Web server
WebServer is a python [flask](http://flask.pocoo.org/) server. It fetches data from twitter using [Tweepy](http://www.tweepy.org/). Tweets are pushed into [Kafka](https://kafka.apache.org/). A sentiment analyzer picks tweets from kafka, performs sentiment analysis using [NLTK](http://www.nltk.org/_modules/nltk/sentiment/vader.html) and pushes the result back in Kafka. Sentiment is read by [Spark Streaming](https://spark.apache.org/streaming/) server (see below), it calculates the rolling average and writes data back in Kafka. In the final step, the web server reads the rolling mean from Kafka and sends it to connected clients via [SocketIo](https://socket.io/). A html/JS client displays the live sentiment in a sparkline graph using [google annotation](https://developers.google.com/chart/interactive/docs/gallery/annotationchart) charts. 

#### 2. Calculating rolling mean of sentiments

An independent java program reads sentiment from Kafka using spark streaming, calculates the rolling average using spark window operations, and writes the results back to Kafka. 

### How to run
To run the project
1. Download, setup and run Apache Kafka. I use following commands on OSX from bin dir of kafka
```
sh zookeeper-server-start.sh ../config/zookeeper.properties
sh kafka-server-start.sh ../config/server.properties
```
2. Install complete [NLTK](http://www.nltk.org/install.html)
3. Create a [twitter app](https://apps.twitter.com/) and set your keys in `live_twitter_sentiment_analysis/webapp/tweet_ingestion/config.py`
4. Install python packages
```
pip install -r /live_twitter_sentiment_analysis/webapp/requirements.txt
```
5. Run webserver
```
python live_twitter_sentiment_analysis/webapp/main.py
```
6. Run the maven-java project (rolling_average) after installing maven dependencies specified in `live_twitter_sentiment_analysis/rolling_average/pom.xml`. Don't forget to set checkpoint dir in Main.java
7. open the url [localhost:8001/index.html](localhost:8001/index.html)
### Output
Here is what final output looks like in browser

![output](https://user-images.githubusercontent.com/1760859/28225813-51a955fc-68ed-11e7-8fc7-40f5a5022ac5.png)

Note: Tested on python 2.7
