#! python3
import sys
import time
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineQueryResultArticle, InputTextMessageContent
from pprint import pprint
import re
import requests
import json
import urllib
import urllib.request
from bs4 import BeautifulSoup
import datetime
from emoji import emojize

import pymongo
from pymongo import MongoClient


APITOKEN = "<API-TOKEN>"
bot = telepot.Bot(APITOKEN)
answerer = telepot.helper.Answerer(bot)

connection_params = {
    'user': '<USERNAME>',
    'password': '<PASSWORD>',
    'host': '<example.mlab.com>',
    'port': 777,
    'namespace': '<DATABASE-NAME>',
}

connection = MongoClient(
    'mongodb://{user}:{password}@{host}:'
    '{port}/{namespace}'.format(**connection_params)
)

db = connection.neaea

userMsg = db.messages
errors = db.errors
botResponse = db.response


def handle(msg):
    try:
        person_id = msg.get('chat').get('id')
        text = msg.get('text')
        bot.sendChatAction(person_id, "typing")
        log(msg)
        userMsg.insert_one(msg)
        if text.startswith('/'):
            bot.sendMessage(
                person_id, "እባክዎ መተርጎም የሚፈልጉትን ጽሑፍ ያስገቡ")
        else:
            result = get_translation(text)
            bot.sendMessage(person_id, result)
            botResponse.insert_one({"person_id:": person_id, "result": result})
    except Exception as e:
        bot.sendMessage(
            person_id, "የሆነ ስህተት ተፈጥሯል, እባክዎ ቆይተው እንደገና ይሞክሩ")
        errors.insert_one({'error':str(e)})
        log("Handle: Error: "+str(e))


def on_inline_query(msg):
    log(msg)
    userMsg.insert_one(msg)
    def compute():
        try:
            query_id, from_id, query_string = telepot.glance(
                msg, flavor='inline_query')
            # print('Inline Query:', query_id, from_id, query_string)
            if len(query_string) >= 6:
                translation = get_translation(query_string)
                articles = [InlineQueryResultArticle(
                    id='abc',
                    title="ተተርጉሟል",
                    input_message_content=InputTextMessageContent(
                        message_text=translation
                    )
                )]
                return articles
            else:
                articles = [InlineQueryResultArticle(
                    id='abc',
                    title='የሆነ ነገር ጻፍ',
                    input_message_content=InputTextMessageContent(
                        message_text="እባክዎ መተርጎም የሚፈልጉትን ጽሑፍ ያስገቡ"
                    )
                )]
                return articles
        except Exception as e:
        	errors.insert_one({'error':str(e)})
        	log(e)
        	return None
    if compute != None:
        try:
            answerer.answer(msg, compute)
        except Exception as e:
        	errors.insert_one({'error':str(e)})
        	log(e)

def on_chosen_inline_result(msg):
    log(msg)
    userMsg.insert_one(msg)
    result_id, from_id, query_string = telepot.glance(
        msg, flavor='chosen_inline_result')
    print('Chosen Inline Result:', result_id, from_id, query_string)


def get_translation(text):

    text = text.strip()
    try:
        pass
    except Exception as e:
    	errors.insert_one({'error':str(e)})
    	log("Get Translation Error: "+str(e))
    	return "የሆነ ስህተት ተፈጥሯል, እባክዎ ቆይተው እንደገና ይሞክሩ \n"


def log(msg):
    with open('log_results.txt', 'a') as logfile:
        now = datetime.datetime.now()
        logfile.write(now.isoformat()+"\t"+str(msg)+"\n\n")


def main():
    MessageLoop(bot, {'chat': handle,
                      'inline_query': on_inline_query,
                      'chosen_inline_result': on_chosen_inline_result}).run_as_thread()

    print('Listening ...')
    log("******************************Server Started at" +
        datetime.datetime.now().isoformat() + "***************************")

    # Keep the program running.
    while 1:
        time.sleep(10)

if __name__ == '__main__':
    main()
