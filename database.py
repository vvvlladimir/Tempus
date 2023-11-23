import datetime
import os

from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient

import log

logger = log.setup_logger("Mongo DB", 1, 1)
# TODO: add validation to DB

load_dotenv(find_dotenv())
MONGO_PWD = os.getenv("MONGO_PWD")
MONGO_LOGIN = os.getenv("MONGO_LOGIN")

cluster = f"mongodb+srv://{MONGO_LOGIN}:{MONGO_PWD}@tempus.oujnava.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(cluster)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    logger.info("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    logger.critical(e)

app = client.app
users = app.users
schedules = app.schedules


def get_user_data(tg_id):
    user = users.find_one({"tg_id": tg_id})

    if user is None:
        user_data = {
            "tg_id": tg_id,
            "name": "-",
            "age": "-",
            "job": "-",
            "job_code": "---",
            "language": "-",
        }
        users.insert_one(user_data)
        logger.debug("// %s // User NOT found")
        return 0
    logger.debug("// %s // User found: %s", tg_id, user)
    return user


def update_job_code(tg_id, new_job_code):
    users.update_one({"tg_id": tg_id}, {"$set": {"job_code": f"{new_job_code}"}})
    logger.debug("// %s // 'job_code' updated successfully!", tg_id)


def change_user_data(tg_id, changes):
    try:
        all_updates = {
            "$set": {
                "name": changes["name"],
                "job": changes["job"],
                "age": changes["age"],
            }
        }

        users.update_one({"tg_id": tg_id}, all_updates)
        changes.clear()

        logger.debug("// %s // Data updated successfully!", tg_id)
        return "Success!"
    except Exception as e:
        changes.clear()

        logger.error("// %s // Data updated with error: %s", tg_id, e)
        return e


def add_new_schedule(tg_id, data):
    try:
        doc = {
            "creation_date": datetime.datetime.now(),
            "dates": data,
            "user_id": tg_id
        }
        schedules.insert_one(doc)
        data.clear()

        logger.debug("// %s // Data updated successfully!", tg_id)
        return "Success!"
    except Exception as e:
        data.clear()

        logger.error("// %s // Data updated with error: %s", tg_id, e)
        return e


def datetime_to_str(date_array):
    formatted_dates = [date.strftime("%Y-%m-%d, %H:%M") for date in date_array]
    str = "\n".join(f"{i + 1}. {formatted_dates[i]}" for i in range(len(formatted_dates)))
    return str


def get_schedule_data(tg_id):
    schedule_data = schedules.find_one({'user_id': tg_id}, sort=[('creation_date', -1)])

    if schedule_data is None:
        schedule_data = {
            "creation_date": '---',
            "dates": "У вас еще нет запланированных рабочих дней!",
        }
    else:
        schedule_data["creation_date"] = schedule_data["creation_date"].strftime("%Y-%m-%d, %H:%M")
        schedule_data["dates"] = datetime_to_str(schedule_data["dates"])

    logger.debug("// %s // Schedule found: %s", tg_id, schedule_data)
    return schedule_data
