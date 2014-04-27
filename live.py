from TwitterAPI import TwitterAPI
import datetime
from threading import Thread
import sys, os

# Imports
import gzip                  # For compression
import cPickle as pickle     # For storing/loading objects to disk
import time		             # How fast are we going?
import os

import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# Set our default plot size
from pylab import *
rcParams['figure.figsize'] = 20, 8

from nltk.classify import NaiveBayesClassifier    # Natural Language Toolkit's Naive Bayes Classifier
from nltk.stem.wordnet import WordNetLemmatizer   # NLTK's work lemmatizer
import nltk.classify.util                         # NLTK etc.

import MySQLdb
import datetime

# Twitter App #1 - For use with TrackTerms
CONSUMER_KEY_Terms = 'ybGIhnu9GPWkzHOJem3Tow'
CONSUMER_SECRET_Terms = 'OUNNpa2Y0yymTQ9KssG5yAvsPc24AunKncLkW7dTBUs'
ACCESS_TOKEN_KEY_Terms = '46986295-4ar0e23athY6MIrQnuwZXawDkCanFykSCDSsc3W1C'
ACCESS_TOKEN_SECRET_Terms = 'A0yyNk3CjlMxQlm8fvAW80gT7xkGxthd94H1Dgz5ygtUe'

realtime_api = TwitterAPI(CONSUMER_KEY_Terms, CONSUMER_SECRET_Terms, ACCESS_TOKEN_KEY_Terms, ACCESS_TOKEN_SECRET_Terms)

# MySQL Stuff
db = MySQLdb.connect(host="localhost", user="pat", passwd="asdfghjkl", db="Twitter")
cursor = db.cursor()


# Stream the ENGLISH sample of the firehose
def SampleStream():
    start = time.time()
    while True:
        try:
            # Select the correct Twitter App to use
            r = realtime_api.request('statuses/sample')
        
            # Parse each English item
            tweetsec = []
            for item in r:
                if 'lang' in item:
                    if item['lang'] == 'en':
                        #print item['text']
                        now = time.time()
                        if now >= start + 1:
                            #print 'will yield'
                            yield tweetsec
                            #print 'did yield'
                            start = now
                            tweetsec = []
                            tweetsec.append(item['text'])
                        else:
                            tweetsec.append(item['text'])
        except:
            print 'dropped'
            
# Create an instance of the Lemmatizer
lmtzr = WordNetLemmatizer()

# Some parts of tweets we just don't care about (#sorry)
ignoreWordBeginnings = ['#', '@', 'http://', 'rt']

# Some Functions we will keep referencing

# Function to *consistently* convert words into a feature set that NLTK can use
def word_feats(words):
	return dict([(lmtzr.lemmatize(word.lower()), True) for word in words])

# Return a list of words, without any hashtags, Twitter handles, links, etc
def CleanWords(aTweet):
    tweetWords = []
    for word in aTweet.strip().split(' '):
        
        output = True
        for prefix in ignoreWordBeginnings:
            if word.lower().startswith(prefix):
                output = False
	
        if output:
            tweetWords.append(word)
            
    #print aTweet, tweetWords
    return tweetWords

# Load the pickled and compressed Sentiment Classifier
with gzip.open('TwitterSentimentClassifier.p','rb') as f:      # READONLY! let's not overwrite our beautiful classifier
	sentimentClassifer = pickle.load(f)
	
for TweetList in SampleStream():
    sentiment = 0
    tweetCount = 0
    for Tweet in TweetList:
        
        # Get sentiment
        tweetWords = CleanWords(Tweet)
        pdist = sentimentClassifer.prob_classify( word_feats(tweetWords) )
            
        pos = pdist.prob('pos')
        neg = pdist.prob('neg')
        
        sent = 0						# Neutral (neither positive nor negative is above the threshold of 55% confidence)
        if pos > .55: sent = 1			# Positive
        elif neg > .55: sent = -1		# Negative
            
        # Store result temporarily
        sentiment += sent
        tweetCount += 1
    
    ## Populate MySQL
    try:
        cursor.execute("INSERT INTO sentiment (id, sentiment, count, ratio, baseline) VALUES(%s, %s, %s, %s, %s);",
               (str(time.time()),
                str(sentiment),
                str(tweetCount),
                str(float(float(sentiment)/float(tweetCount))),
                str(0)
                )
               )
        db.commit()
    except:
        db.rollback()
