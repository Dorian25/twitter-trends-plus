import json
import os
import re

import pandas as pd
import tweepy
import yake
# nltk.download("vader_lexicon")
# from pattern.fr import sentiment
from flask import Flask, render_template, request, url_for
from textblob import TextBlob
from deep_translator import GoogleTranslator

#from wordcloud import WordCloud, STOPWORDS
#from langdetect import detect

app = Flask(__name__)

# initialize api instance
consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
consumer_secret = os.environ.get("TWITTER_CONSUMER_KEY_SECRET")
access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

#Connect to Twitter through the API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

df_countries = pd.read_csv("static/country_lang.csv")
with open("static/stopwords-all.json", encoding='utf-8') as f:
   stopwords_all = json.load(f)


def get_woeid(place):
    '''Get woeid by location'''
    try:
        trends = api.available_trends()
        for val in trends:
            if (val['parentid'] == 1) and (val['country'].lower() == place.lower()):
                return(val['woeid'])
        print('Location Not Found')
    except Exception as e:
        print('Exception:', e)
        return(0)


def get_country_code(country_name):
    country_code = df_countries.loc[df_countries["country_name"] == country_name, "country_code"].values[0]
    return country_code


def get_country_lang(country_name):
    lang = df_countries.loc[df_countries["country_name"] == country_name, "lang"].values[0]

    if "/" in lang:
        langs = lang.split("/")
        return langs[0]
    else:
        return lang


def get_country_dict(country_name):
    return {'country_name': country_name,
            'country_code': get_country_code(country_name),
            'country_lang': get_country_lang(country_name)}


def get_stopwords(lang):
    return set(stopwords_all[lang])


def preprocess_tweet(tweet, trend):
    # source :
    # https://berkeley-stat159-f17.github.io/stat159-f17/lectures/11-strings/11-nltk..html#First-pass
    #print(tweet)
    # Trend removal
    tweet = re.sub(trend, "", tweet)
    # URL removal
    tweet = re.sub(r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))", "", tweet)
    # Mention removal
    tweet = re.sub(r"@\w+", "", tweet)
    # Hashtag removal
    tweet = re.sub(r"#\w+", "", tweet)
    # Emoticon removal
    #tweet = re.sub(r"[^\x01-\x7F]", "", tweet)
    # Carriage removal
    tweet = re.sub(r"[\r\n]", "", tweet)
    # Double space removal
    tweet = re.sub('\s+', ' ', tweet).strip()
    # Tokenizer
    #tokenizer = TweetTokenizer()
    #tweet_token = tokenizer.tokenize(tweet.lower())
    #print(tweet_token)
    # Punctations removal
    #tweet = "".join([char.lower() for char in tweet if char not in string.punctuation])

    return tweet


def sentiment_trend(tweets):
    # source
    # https://towardsdatascience.com/step-by-step-twitter-sentiment-analysis-in-python-d6f650ade58d
    # https://github.com/cjhutto/vaderSentiment
    positive = 0
    negative = 0
    neutral = 0
    polarity = 0
    tweet_list = []
    neutral_list = []
    negative_list = []
    positive_list = []

    for tweet in tweets:

        tweet_translated = GoogleTranslator(source='auto', target='en').translate(tweet.full_text)
        print(tweet_translated)
        analysis = TextBlob(tweet_translated)

        if analysis.sentiment.polarity > 0:
            positive += 1
        elif analysis.sentiment.polarity == 0:
            neutral += 1
        else:
            negative += 1

        txt = "C'est un jour magnifique"
        #print(TextBlob(txt).sentiment.polarity)

        """
        score = SentimentIntensityAnalyzer().polarity_scores(tweet.full_text)
        neg = score['neg']
        neu = score['neu']
        pos = score['pos']
        comp = score['compound']
        polarity += analysis.sentiment.polarity

        if neg > pos:
            negative_list.append(tweet.full_text)
            negative += 1
        elif pos > neg:
            positive_list.append(tweet.full_text)
            positive += 1

        elif pos == neg:
            neutral_list.append(tweet.full_text)
            neutral += 1
        """

    return positive, neutral, negative


def popular_tweet_trend(tweets):
    max_fav = 0
    oembed_tweet = ""

    for tweet in tweets:
        if tweet.favorite_count > max_fav:
            max_fav = tweet.favorite_count
            # source : https://stackoverflow.com/questions/61918965/get-tweet-url-or-tweet-id-using-tweepy
            # source :
            oembed_tweet = api.get_oembed("https://twitter.com/twitter/statuses/" + str(tweet._json["id"]))

    return oembed_tweet


def media_trend(tweets):
    url_media = []

    for tweet in tweets:
        if 'media' in tweet._json["entities"]:
            if len(tweet._json["entities"]['media']) > 1:
                for media in tweet._json["entities"]['media']:
                    url_media.append(media['media_url_https'])
            else:
                url_media.append(tweet._json["entities"]['media'][0]['media_url_https'])

    return url_media[:5]


def person_trend(trend, lang):
    tweets = tweepy.Cursor(api.search_tweets,
                           q=trend,
                           tweet_mode='extended',
                           lang=lang).items(100)


    #TODO : il faut déterminer une période de temps selon les tweets populaires
    # heure de début de la trend
    # intervalle de 1h ou 2h pour récupérer 1000-2500 tweets

    user_mentions = {}
    hashtags_mentions = {}

    for tweet in tweets:
        print(tweet._json["entities"])
        u_m = tweet._json["entities"]["user_mentions"]
        ht = tweet._json["entities"]["hashtags"]

        if len(u_m) > 0:
            for u in u_m:
                if u['name'] in user_mentions:
                    user_mentions[u['name']] += 1
                else:
                    user_mentions[u['name']] = 1

        if len(ht) > 0:
            for h in ht:
                if h['text'] in hashtags_mentions:
                    hashtags_mentions[h['text']] += 1
                else:
                    hashtags_mentions[h['text']] = 1

    print()
    print("hashtag", dict(sorted(hashtags_mentions.items(), key=lambda item: item[1], reverse=True)))
    print("user mentions", dict(sorted(user_mentions.items(), key=lambda item: item[1], reverse=True)))
    return 0


def summerize_trend(trend, lang, tweets):
    list_tweets = []
    txt = ""
    for tweet in tweets:
        #list_tweets.append(preprocess_tweet(t.full_text, trend))
        #txt += preprocess_tweet(tweet.full_text, trend) + "."
        txt += tweet.full_text + "."


    # Uses stopwords for english from NLTK, and all puntuation characters by
    # default
    #r = Rake(stopwords=get_stopwords(lang),
    #         include_repeated_phrases=False,
    #         )

    # Extraction given the text.
    #r.extract_keywords_from_text(txt)

    # Extraction given the list of strings where each string is a sentence.
    #r.extract_keywords_from_sentences(list_tweets)

    # To get keyword phrases ranked highest to lowest.
    #phrase_df = pd.DataFrame(r.get_ranked_phrases_with_scores()[:10], columns=['score','phrase'])
    #kw_rake = phrase_df.loc[phrase_df.score > 3]['phrase']

    # To get keyword phrases ranked highest to lowest with scores.
    #r.get_ranked_phrases_with_scores()

    #yake (fast)
    max_ngram_size = 3
    deduplication_threshold = 0.9
    windowSize = 1
    numOfKeywords = 10
    deduplication_algo = 'seqm'

    kw_extractor = yake.KeywordExtractorcustom_kw_extractor = yake.KeywordExtractor(lan=lang,
                                                                                    n=max_ngram_size,
                                                                                    dedupLim=deduplication_threshold,
                                                                                    dedupFunc=deduplication_algo,
                                                                                    windowsSize=windowSize,
                                                                                    top=numOfKeywords,
                                                                                    features=None)
    kw_yake = kw_extractor.extract_keywords(txt)

    #textrank
    #kw_textrank = " ".join([kw for kw, s in keywords.keywords(txt, scores=True)])

    #kw_model = KeyBERT()
    #kw_keybert = [kw for kw, s in kw_model.extract_keywords(txt, top_n=10, keyphrase_ngram_range=(1, 3), stop_words=None)]

    return kw_yake


#https://www.unite.ai/10-best-python-libraries-for-sentiment-analysis/


# cmd
# .\venv\Scripts\python.exe -m flask --debug run

@app.route('/', methods=['GET', 'POST'])
def index():
    trends = []
    country_dict = {}

    if request.method == 'POST':
        country_selected = request.form.get('country_select')
        country_dict = get_country_dict(country_selected)
        lang = get_country_lang(country_selected)

        trends_country = api.get_place_trends(get_woeid(country_selected))[0]['trends']

        rank = 1
        for trend in trends_country[:10]:

            popular_tweets = list(tweepy.Cursor(api.search_tweets,
                                           q=trend["name"],
                                           result_type='popular',
                                           tweet_mode='extended',
                                           lang=lang).items())

            trends.append({"rank": rank,
                           "name": trend["name"],
                           "query": trend["query"],
                           "tweet_volume": trend["tweet_volume"],
                           #"keywords": summerize_trend(trend["name"], lang, popular_tweets),
                           "media": media_trend(popular_tweets),
                           "sentiment": sentiment_trend(popular_tweets),
                           "popular_tweet": popular_tweet_trend(popular_tweets)
                           })
            rank += 1

    return render_template("index.html",
                           trends=trends,
                           list_countries=df_countries["country_name"],
                           list_countries_code=",".join(df_countries["country_code"]),
                           country_dict=country_dict)


if __name__ == '__main__':
    app.run(debug=True, host='localhost', threaded=True)

