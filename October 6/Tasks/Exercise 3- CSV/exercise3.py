import csv
import pandas as pd
import logging
#configure logging
logging.basicConfig(filename="csv_app.log",
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
data=[
    ['product','price','quantity'],
    ['Laptop',70000,2],
    ['Mouse',500,5],
    ['Keyboard',1200,3]
]
with open("sales.csv",'w',newline='') as f:
    writer = csv.writer(f)
    writer.writerows(data)

try:
    df=pd.read_csv('sales.csv')
except FileNotFoundError:
    print("sales.csv not found")
try:
    df['total_sales']=df['price']*df['quantity']
except TypeError:
    print("invalid number in columns")
total_lap=df.loc[0,'total_sales']
logging.info(f'Laptop sales = {total_lap}')
total_key=df.loc[1,'total_sales']
logging.info(f'Keyboard sales = {total_key}')
total_mou=df.loc[2,'total_sales']
logging.info(f'Mouse sales = {total_mou}')
print("Laptop total = ",total_lap)
print("Keyboard total = ",total_key)
print("Mouse total = ",total_mou)
