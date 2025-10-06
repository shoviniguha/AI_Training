import yaml
import logging

#configure logging
logging.basicConfig(filename="yaml_app.log",
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
#python dictionary
config={
"app":
    {"name": "Student Portal",
    "version": "1.0"},
"database":
    {"host":" localhost",
    "port": "3306",
    "user": "root"}
}

#write to a json file
with open("config.yaml",'w') as f:
    yaml.dump(config,f)

#read from json file
try:
    with open("config.yaml",'r') as f:
        data = yaml.safe_load(f)
        logging.info('config loaded successfully')
        print('config loaded successfully')
        host=data['database']['host']
        port=data['database']['port']
        user= data['database']['user']
        print("Connecting to ",host,":",port,"as",user)
except FileNotFoundError:
    logging.error('config.yaml not found')
    print("config.yaml not found")