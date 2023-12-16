import datetime as dt
import os

from bson.objectid import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

from utils import log

# TODO: add validation to DB

# Set up logger for MongoDB interactions
logger = log.setup_logger("Mongo DB", 1, 1)

# Load environmental variables from .env file
load_dotenv("./utils/.env")

# Retrieve MongoDB credentials from environmental variables
MONGO_PWD = os.getenv("MONGO_PWD")
MONGO_LOGIN = os.getenv("MONGO_LOGIN")

# Establish connection to MongoDB cluster
cluster = f"mongodb+srv://{MONGO_LOGIN}:{MONGO_PWD}@tempus.oujnava.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(cluster)

# Test MongoDB connection
try:
    client.admin.command('ping')
    logger.info("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    logger.critical(e)

# Define database and collections
app = client.app
users = app.users
schedules = app.schedules


# Function to convert datetime objects to strings
async def datetime_to_str(date_array: list):
    string_data = ''
    index = 0
    for date in date_array:
        formatted_date = date.strftime("%Y-%m-%d, %H:%M")

        # Check if date is in the past or future
        if date < dt.datetime.now():
            string_data += f"{index + 1}. {formatted_date} ✔\n"
        else:
            string_data += f"{index + 1}. {formatted_date}\n"
        index += 1
    return string_data


# Function to retrieve or create user data based on Telegram ID
async def get_user_data(tg_id: int):
    user = users.find_one({"tg_id": tg_id})

    # Create new user if not existing
    if user is None:
        user_data = {
            "tg_id": tg_id,
            "name": "-",
            "age": "-",
            "job": "-",
            "job_code": "-",
            "language": "-",
        }
        users.insert_one(user_data)
        logger.debug("// %s // User created!", tg_id)
        return False

    logger.debug("// %s // User found: %s", tg_id, user)
    # Format notification dates if present
    if "notify_creation_date" and "notifications" in user:
        user["notify_creation_date"] = user["notify_creation_date"].strftime("%Y-%m-%d, %H:%M")
        user["notifications"] = await datetime_to_str(user["notifications"])

    return user


# Function to update a user's job code
async def update_job_code(tg_id: int, new_job_code: str):
    try:
        users.update_one({"tg_id": tg_id}, {"$set": {"job_code": f"{new_job_code}"}})
        logger.debug("// %s // 'job_code' updated successfully!", tg_id)
        return True
    except Exception as e:
        logger.error("// %s // Data updated with error: %s", tg_id, e)
        return False


# Function to change user data based on provided changes
async def change_user_data(tg_id: int, changes: dict):
    changes = {"$set": changes}
    try:
        users.update_one({"tg_id": tg_id}, changes)
        logger.debug("// %s // Data updated successfully!", tg_id)
        return "Success!"
    except Exception as e:
        logger.error("// %s // Data updated with error: %s", tg_id, e)
        return e


# Function to add or update user notification settings
async def add_new_notify_user(tg_id: int, data: dict):
    try:
        doc = {
            "notify_creation_date": dt.datetime.now(),
            "notifications": data,
        }
        changes = {"$set": doc}

        users.update_one({"tg_id": tg_id}, changes)
        logger.debug("// %s // Data updated successfully!", tg_id)
        return True
    except Exception as e:
        logger.error("// %s // Data updated with error: %s", tg_id, e)
        return False


# Function to retrieve or create a user's schedule data
async def get_schedule_data(tg_id: int):
    schedule = schedules.find_one({'tg_id': tg_id}, sort=[('creation_date', -1)])

    # Create a new schedule if none exists or if it's outdated
    if schedule is None or schedule['creation_date'].month != dt.datetime.now().month:
        schedule_data = {
            "tg_id": tg_id,
            "creation_date": dt.datetime.now()
        }
        schedule = {"_id": schedules.insert_one(schedule_data).inserted_id}
        logger.debug("// %s // Schedule created!", tg_id)

    logger.debug("// %s // Schedule found: %s", tg_id, schedule)
    return schedule


# Function to add timestamps to a user's schedule
# TODO: allow to change the date data
async def make_schedule_time_stamp(tg_id: int, user_start_date: str = None, user_end_date: str = None):
    schedule_data = await get_schedule_data(tg_id)
    try:
        _id = ObjectId(schedule_data["_id"])
        dates_to_update = [dt.datetime.now()] if not (user_start_date and user_end_date) else [user_start_date,
                                                                                               user_end_date]
        for date in dates_to_update:
            schedules.update_one({"_id": _id}, {"$push": {"date": date}})
        logger.debug("// %s // Time stamp updated successfully!", tg_id)
    except Exception as e:
        logger.error("// %s // Time stamp updated with error: %s", tg_id, e)
        return False

    return True
