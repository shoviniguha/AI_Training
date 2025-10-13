import pandas as pd
from datetime import datetime

def run_pipeline():
    customers=pd.read_csv("customers.csv")
    orders = pd.read_csv("orders.csv")
    products = pd.read_csv("products.csv")
    customers_orders = pd.merge(customers, orders, on='CustomerID', how='inner')
    df=pd.merge(products, customers_orders, on='ProductID', how='inner')
    df['OrderDate'] = pd.to_datetime(df['OrderDate'])
    df["TotalAmount"]=df["Price"]*df["Quantity"]
    df["OrderMonth"]=df["OrderDate"].dt.month
    df=df[df['Quantity']>=2]
    df = df[df["Country"].isin(["India", "UAE"])]
    df=df.sort_values(by="TotalAmount", ascending=False)
    tot_rev_cat=df.groupby('Category')['TotalAmount'].sum()
    tot_rev_cat=tot_rev_cat.reset_index()
    tot_rev_cust = df.groupby('Segment')['TotalAmount'].sum()
    tot_rev_cust = tot_rev_cust.reset_index()
    df.to_csv("processed_orders.csv",index=False)
    tot_rev_cat.to_csv("category_summary.csv", index=False)
    tot_rev_cust.to_csv("segment_summary.csv", index=False)
    print(f"Pipeline completed at {datetime.now()}")

if __name__=="__main__":
    run_pipeline()
