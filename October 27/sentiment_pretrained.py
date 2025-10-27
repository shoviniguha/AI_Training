from transformers import pipeline
sentiment_pipeline = pipeline(model="finiteautomata/bertweet-base-sentiment-analysis")
data = ["This is a good book", "This book could have been much better"]
results=sentiment_pipeline(data)
print(results)