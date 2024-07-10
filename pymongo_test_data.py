import pymongo
import time
import os

def build_mongo_client_and_collection():
    user = os.environ.get("MONGO_INITDB_ROOT_USERNAME", "admin")
    cred = os.environ.get("MONGO_INITDB_ROOT_USERNAME", "mypassword")
    host = os.environ.get("MONGO_HOST", "water-rights-visualizer-water_mongo-1")
    #host = os.environ.get("MONGO_HOST", "localhost")
    port = os.environ.get("MONGO_PORT", 27017)

    database = os.environ.get("MONGO_DATABASE", "water")
    collection = os.environ.get("MONGO_COLLECTION", "report_queue")

    mongo_str = 'mongodb://{}:{}@{}:{}'.format(user, cred, host, port)
    
    client = pymongo.MongoClient(
        host = host,
        username = user,
        password = cred,
        port = port        
    )

    db = client[database]
    collect = db[collection]
    
    return collect
    
def populate_test_data():
    print("Populating test data")
    
    collect = build_mongo_client_and_collection()    
        
    for record in get_test_data():
        key = record['key']
        print("Creating test record for: {}".format(key))
        
        db_filter = { 'key' : key }
        collect.replace_one(db_filter, record, upsert=True)
        
def get_test_data():    
    data = [
        {
            "key": "Smith_2019_2020_1717445252512",
            "name": "Smith",
            "cmd": "/opt/conda/bin/python /app/water-rights-visualizer-backend-S3.py /root/data/water_rights_runs/Smith_2019_2020_1717445252512/config.json",
            "status": "Complete",
            "status_msg": "Success",
            "submitted": 1717445252512,
            "started": 1717445294123,
            "ended": 1717445961123,
            "pid": 111,
            "invoker": "to-do",
            "base_dir": "/root/data/water_rights_runs/Smith_2019_2020_1717445252512",
            "png_dir": "/root/data/water_rights_runs/Smith_2019_2020_1717445252512/output/figures/Smith",
            "csv_dir": "/root/data/water_rights_runs/Smith_2019_2020_1717445252512/output/monthly_nan/Smith",
            "subset_dir": "/root/data/water_rights_runs/Smith_2019_2020_1717445252512/output/subset/Smith",
            "geo_json": "/root/data/water_rights_runs/Smith_2019_2020_1717445252512/Smith.geojson",
            "start_year": 2019,
            "end_year": 2020
        },
        {
            "key": "Smith_1988_1990_1717445286267",
            "name": "Smith",
            "cmd": "/opt/conda/bin/pythonNNNzzzz /app/water-rights-visualizer-backend-S3.py /root/data/water_rights_runs/Smith_1988_1990_1717445286267/config.json",
            "status": "Failed",
            "status_msg": "[Errno 2] No such file or directory: '/opt/conda/bin/pythonNNNzzzz'",
            "submitted": 1717445286267,
            "started": 1717446021123,
            "ended": 1717446021123,
            "pid": 222,
            "invoker": "to-do",
            "base_dir": "/root/data/water_rights_runs/Smith_1988_1990_1717445286267",
            "png_dir": "/root/data/water_rights_runs/Smith_1988_1990_1717445286267/output/figures/Smith",
            "csv_dir": "/root/data/water_rights_runs/Smith_1988_1990_1717445286267/output/monthly_nan/Smith",
            "subset_dir": "/root/data/water_rights_runs/Smith_1988_1990_1717445286267/output/subset/Smith",
            "geo_json": "/root/data/water_rights_runs/Smith_1988_1990_1717445286267/Smith.geojson",
            "start_year": 1988,
            "end_year": 1990
        },
        {
            "key": "target_1990_1991_1717445309671",
            "name": "target",
            "cmd": "/opt/conda/bin/python /app/water-rights-visualizer-backend-S3.py /root/data/water_rights_runs/target_1990_1991_1717445309671/config.json",
            "status": "Pending",
            "status_msg": None,
            "submitted": int(time.time() * 1000),
            "started": None,
            "ended": None,
            "pid": 123,
            "invoker": "to-do",
            "base_dir": "/root/data/water_rights_runs/target_1990_1991_1717445309671",
            "png_dir": "/root/data/water_rights_runs/target_1990_1991_1717445309671/output/figures/target",
            "csv_dir": "/root/data/water_rights_runs/target_1990_1991_1717445309671/output/monthly_nan/target",
            "subset_dir": "/root/data/water_rights_runs/target_1990_1991_1717445309671/output/subset/target",
            "geo_json": "/root/data/water_rights_runs/target_1990_1991_1717445309671/target.geojson",
            "start_year": 1990,
            "end_year": 1991
        },
        {
            "key": "target_2001_2002_1717445349510",
            "name": "target",
            "cmd": "/opt/conda/bin/python /app/water-rights-visualizer-backend-S3.py /root/data/water_rights_runs/target_2001_2002_1717445349510/config.json",
            "status": "Pending",
            "status_msg": None,
            "submitted": int(time.time() * 1000) + 9001, #make this different than the record above
            "started": None,
            "ended": None,
            "pid": None,
            "invoker": "to-do",
            "base_dir": "/root/data/water_rights_runs/target_2001_2002_1717445349510",
            "png_dir": "/root/data/water_rights_runs/target_2001_2002_1717445349510/output/figures/target",
            "csv_dir": "/root/data/water_rights_runs/target_2001_2002_1717445349510/output/monthly_nan/target",
            "subset_dir": "/root/data/water_rights_runs/target_2001_2002_1717445349510/output/subset/target",
            "geo_json": "/root/data/water_rights_runs/target_2001_2002_1717445349510/target.geojson",
            "start_year": 2001,
            "end_year": 2002
        }
    ]
    
    return data

if __name__ == '__main__':    
    populate_test_data()