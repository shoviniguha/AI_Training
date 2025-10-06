import configparser

config=configparser.ConfigParser()
config['database']={
    "host":"localhost",
    "port":"3306",
    "user":"root",
    "password":"admin123"
}

with open("app.ini",'w') as f:
    config.write(f)

config.read("app.ini")

print(config["database"]["host"])