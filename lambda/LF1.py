import math
import dateutil.parser
import datetime
import time
import os
from botocore.vendored import requests
import logging

import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

""" --- Helper Functions --- """

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def isvalid_number(number):
    try:
        if not number:
            return True
        val = int(number)
        return True
    except ValueError:
        return False

"""
DiningLocation
CuisineType
PeopleNumber
DiningDate
DiningTime
PhoneNumber
"""

def validate_suggest_restaurants(dining_location, cuisine_type, people_number, dining_date, dining_time):
    cuisine_types = ['japanese', 'chinese', 'indian']
    if cuisine_type is not None and cuisine_type.lower() not in cuisine_types:
        return build_validation_result(False,
                                       'CuisineType',
                                       'We do not have {}, would you like a different type of cuisine?  '
                                       'Our most popular cuisine type is Japanese'.format(cuisine_type))

    if not isvalid_number(people_number):
        return build_validation_result(False, 'PeopleNumber', 'I did not understand that, please input a number?')

    if dining_date is not None:
        if not isvalid_date(dining_date):
            return build_validation_result(False, 'DiningDate', 'I did not understand that, what date would you like to eat?')
        elif datetime.datetime.strptime(dining_date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(False, 'DiningDate', 'You can choose a date from tomorrow onwards.  What day would you like to eat?')

    if dining_time is not None:
        if len(dining_time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        hour, minute = dining_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        if hour < 10 or hour > 16:
            # Outside of business hours
            return build_validation_result(False, 'DiningTime', 'Our business hours are from ten a m. to five p m. Can you specify a time during this range?')

    return build_validation_result(True, None, None)


def greeting_intent(intent_request):
    source = intent_request['invocationSource']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Hi there, how can I help?'})


def thank_you_intent(intent_request):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Glad to help.'})

def suggest_restaurants(intent_request):

    dining_location = get_slots(intent_request)["DiningLocation"]
    cuisine_type = get_slots(intent_request)["CuisineType"]
    people_number = get_slots(intent_request)["PeopleNumber"]
    dining_date = get_slots(intent_request)["DiningDate"]
    dining_time = get_slots(intent_request)["DiningTime"]
    # phone_number = get_slots(intent_request)["PhoneNumber"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)

        validation_result = validate_suggest_restaurants(dining_location, cuisine_type, people_number, dining_date, dining_time)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        return delegate(output_session_attributes, get_slots(intent_request))

    URL="https://api.yelp.com/v3/businesses/search"
    HEADERS = {'authorization': "Bearer Ua9rqEm2CoRIr7YJuIYmt7nYVZ1fmyejc3qTIGw-h5dcIb2iFK2goYn9l3gY7xNLHodJZKDKw7XljTobZenuySMr7E4R-7Cni6iBe-1Z9D1HtweFPuPV8FwVmHx0XHYx"}
    PARAMS = {
        "location":dining_location,
        "limit":"3",
        "categories": cuisine_type+", food"
    }
    r = requests.get(url=URL,headers=HEADERS,params=PARAMS)
    data = r.json()
    restaurant_list = data['businesses']
    restaurant_1 = restaurant_list[0]
    restaurant_2 = restaurant_list[1]
    restaurant_3 = restaurant_list[2]
    suggestions = 'Here are my '+cuisine_type+' restaurant suggestions for '+people_number+' people, for '+dining_date+' at '+dining_time+': 1. ' + restaurant_1['name'] +', located at '+ restaurant_1['location']['address1']+'. 2. ' + restaurant_2['name'] +', located at '+ restaurant_2['location']['address1']+'. 3. ' + restaurant_3['name'] +', located at '+ restaurant_3['location']['address1']+'. Enjoy your meal!'

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': suggestions})

def dispatch(intent_request):
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    if intent_name == 'SuggestRestaurants':
        return suggest_restaurants(intent_request)
    elif intent_name == 'GreetingIntent':
        return greeting_intent(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank_you_intent(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')

def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
