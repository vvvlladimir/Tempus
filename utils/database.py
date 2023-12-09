import datetime as dt
import os
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId

from utils import log

logger = log.setup_logger("Mongo DB", 1, 1)
# TODO: add validation to DB

load_dotenv(find_dotenv())
MONGO_PWD = os.getenv("MONGO_PWD")
MONGO_LOGIN = os.getenv("MONGO_LOGIN")

cluster = f"mongodb+srv://{MONGO_LOGIN}:{MONGO_PWD}@tempus.oujnava.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(cluster)

try:
    client.admin.command('ping')
    logger.info("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    logger.critical(e)

app = client.app
users = app.users
schedules = app.schedules


async def datetime_to_str(date_array: list):
    string_data = ''
    index = 0
    for date in date_array:
        formatted_date = date.strftime("%Y-%m-%d, %H:%M")

        if (date < dt.datetime.now()):
            string_data += f"{index + 1}. {formatted_date} ✔\n"
        else:
            string_data += f"{index + 1}. {formatted_date}\n"
        index += 1
    return string_data


# -----------------------------------------------------------------------

async def get_user_data(tg_id: int):
    user = users.find_one({"tg_id": tg_id})

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
        logger.debug("// %s // User NOT found")
        return 0
    logger.debug("// %s // User found: %s", tg_id, user)
    return user


async def update_job_code(tg_id: int, new_job_code: str) -> None:
    users.update_one({"tg_id": tg_id}, {"$set": {"job_code": f"{new_job_code}"}})
    logger.debug("// %s // 'job_code' updated successfully!", tg_id)


async def change_user_data(tg_id: int, changes: dict):
    changes = {"$set": changes}
    # print(changes)
    try:
        users.update_one({"tg_id": tg_id}, changes)

        logger.debug("// %s // Data updated successfully!", tg_id)
        return "Success!"
    except Exception as e:

        logger.error("// %s // Data updated with error: %s", tg_id, e)
        return e


async def add_new_schedule(tg_id: int, data: dict):
    try:
        doc = {
            "creation_date": dt.datetime.now(),
            "notifications": data,
            "user_id": tg_id
        }

        # Checking if we have the schedule in the same month
        old_creation_date = await get_schedule_data(tg_id, True)
        if old_creation_date and old_creation_date["creation_date"].month == dt.datetime.now().month:
            _id = ObjectId(old_creation_date["_id"])
            schedules.delete_one({"_id": _id})

        schedules.insert_one(doc)

        logger.debug("// %s // Data updated successfully!", tg_id)
        return "Success!"
    except Exception as e:
        logger.error("// %s // Data updated with error: %s", tg_id, e)
        return e


async def get_schedule_data(tg_id: int, pure: bool = False):
    schedule_data = schedules.find_one({'user_id': tg_id}, sort=[('creation_date', -1)])

    if schedule_data is None:
        logger.debug("// %s // Schedule NOT found.", tg_id)
        return False

    if pure:
        logger.debug("// %s // Schedule found: %s", tg_id, schedule_data)
        return schedule_data

    schedule_data["creation_date"] = schedule_data["creation_date"].strftime("%Y-%m-%d, %H:%M")
    schedule_data["notifications"] = await datetime_to_str(schedule_data["notifications"])
    logger.debug("// %s // Schedule found: %s", tg_id, schedule_data)

    return schedule_data


# TODO: check if user send more than 1 time stamp and allow to change the date data
async def make_schedule_time_stamp(tg_id: int, user_date: str = None):
    schedule_data = await get_schedule_data(tg_id, True)
    if schedule_data is False:
        return False
    try:
        # if user_date is not None:
        #     pass
        _id = ObjectId(schedule_data["_id"])
        date = {"date": dt.datetime.now()}
        changes = {"$push": date}
        schedules.update_one({"_id": _id}, changes)

        logger.debug("// %s // Time stamp updated successfully!", tg_id)
    except Exception as e:
        logger.error("// %s // Time stamp updated with error: %s", tg_id, e)
        return e
    return True
