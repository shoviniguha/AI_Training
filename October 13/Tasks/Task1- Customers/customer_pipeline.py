import pandas as pd
from datetime import datetime

def run_pipeline():
    df=pd.read_csv("customers.csv")
    df["Age Group"]=df['Age'].apply(lambda x: "Young" if x<30 else ("Adult" if 30<=x<50 else "Senior" ))
    df_filtered=df[df["Age"]>=20]
    df_filtered.to_csv("filtered_customers.csv",index=False)
    print(f"Pipeline completed at {datetime.now()}")

if __name__=="__main__":
    run_pipeline()