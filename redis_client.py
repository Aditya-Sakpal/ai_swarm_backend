import os 
import dotenv
import redis

dotenv.load_dotenv()

redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), password=os.getenv("REDIS_PASSWORD"), db=0, decode_responses=True)