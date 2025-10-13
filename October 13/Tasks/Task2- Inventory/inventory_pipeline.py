import pandas as pd
from datetime import datetime

def run_pipeline():
    df=pd.read_csv("inventory.csv")
    df["RestockNeeded"] = df.apply(lambda x: "Yes" if x["Quantity"]<x["ReorderLevel"] else "No",axis=1)
    df["TotalValue"]=df['Quantity']*df["PricePerUnit"]
    df.to_csv("restock_report.csv",index=False)
    print(f"Inventory Pipeline completed at {datetime.now()}")

if __name__=="__main__":
    run_pipeline()