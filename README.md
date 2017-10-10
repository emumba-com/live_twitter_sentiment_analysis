# Scalable architecture for real-time Twitter sentiment analysis
This project implements a scalable architecture to monitor and visualize sentiment against a twitter hashtag in real-time. It streams live tweets from Twitter against a hashtag, performs sentiment analysis on each tweet, and calculates the rolling mean of sentiments. This sentiment mean is continuously sent to connected browser clients and displayed in a sparkline graph. 

### System design
Diagram below illustrates different components and information flow (from right to left).
![system design](https://user-images.githubusercontent.com/1760859/28240920-5a8ed604-69a3-11e7-95e1-38a6ddb43f7c.png)

### Project breakdown
Project has three parts

#### 1. Web server
WebServer is a python [flask](http://flask.pocoo.org/) server. It fetches data from twitter using [Tweepy](http://www.tweepy.org/). Tweets are pushed into [Kafka](https://kafka.apache.org/). A sentiment analyzer picks tweets from kafka, performs sentiment analysis using [NLTK](http://www.nltk.org/_modules/nltk/sentiment/vader.html) and pushes the result back in Kafka. Sentiment is read by [Spark Streaming](https://spark.apache.org/streaming/) server (part 3), it calculates the rolling average and writes data back in Kafka. In the final step, the web server reads the rolling mean from Kafka and sends it to connected clients via [SocketIo](https://socket.io/). A html/JS client displays the live sentiment in a sparkline graph using [google annotation](https://developers.google.com/chart/interactive/docs/gallery/annotationchart) charts. 

Web server runs each independent task in a separate thread.<br>
**Thread 1**: fetches data from twitter<br>
**Thread 2**: performs sentiment analysis on each tweet<br>
**Thread 3**: looks for rolling mean from spark streaming<br>

All these threads can run as an independent service to provide a scalable and fault tolerant system. 

#### 2. Kafka
Kafka acts as a message broker between different modules running within the web server as well as between web server and spark streaming server. It provides a scalable and fault tolerant mechanism of communication between independently running services.  

#### 3. Calculating rolling mean of sentiments

A separate java program reads sentiment from Kafka using spark streaming, calculates the rolling average using spark window operations, and writes the results back to Kafka. 

### How to run
To run the project
1. Download, setup and run Apache Kafka. I use following commands on OSX from bin dir of kafka
```
sh zookeeper-server-start.sh ../config/zookeeper.properties
sh kafka-server-start.sh ../config/server.properties
```
2. Install complete [NLTK](http://www.nltk.org/install.html)
3. Create a [twitter app](https://apps.twitter.com/) and set your keys in<br> `live_twitter_sentiment_analysis/webapp/tweet_ingestion/config.py`
4. Install python packages
```
pip install -r /live_twitter_sentiment_analysis/webapp/requirements.txt
```
5. Run webserver
```
python live_twitter_sentiment_analysis/webapp/main.py
```
6. Run the maven-java project (rolling_average) after installing maven dependencies specified in `live_twitter_sentiment_analysis/rolling_average/pom.xml`. Don't forget to set checkpoint dir in Main.java
7. open the url `localhost:8001/index.html`
### Output
Here is what final output looks like in browser

![output](https://user-images.githubusercontent.com/1760859/30729488-69da0d02-9f79-11e7-9fea-2e6c411f8565.png)

Note: Tested on python 2.7
