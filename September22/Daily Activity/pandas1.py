import pandas as pd

data = {
    "Name": ["Rahul", "Priya", "Arjun", "Neha", "Vikram"],
    "Age": [21, 22, 20, 23, 21],
    "Course": ["AI", "ML", "Data Science", "AI", "ML"],
    "Marks": [85, 90, 78, 88, 95]
}
df=pd.DataFrame(data)
print(df)

print(df['Name'])   #selecting a column
print(df[['Name','Marks']])   #selecting two columns
print(df.iloc[0])   #first row
print(df.loc[2,'Marks'])   #value at row2 and column marks