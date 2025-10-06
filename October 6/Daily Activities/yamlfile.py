import yaml

#python dictionary
config={
    "model":"RandomForest",
    "age":21,
    "params":{"max_depth":5,"n_estimators":100},
    "dataset":"students.csv"
}

#write to a json file
with open("config.yaml",'w') as f:
    yaml.dump(config,f)

#read from json file
with open("config.yaml",'r') as f:
    data = yaml.safe_load(f)

print(data["params"]["n_estimators"])