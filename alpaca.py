import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ['ALPACA_API_KEY']
API_SECRET = os.environ['ALPACA_API_SECRET']
APCA_API_BASE_URL = "https://paper-api.alpaca.markets/v2"


def create_url():
    return APCA_API_BASE_URL + '/orders'


def create_headers():
    headers = {"APCA-API-KEY-ID": API_KEY, "APCA-API-SECRET-KEY": API_SECRET}
    return headers


def create_data(ticker, side, notional, buy_target, take_profit, stop_loss):
    qty = notional // buy_target
    data = {
        "symbol": ticker,
        "side": side,
        "type": 'limit',
        "qty": qty,
        "time_in_force": 'gtc',
        "limit_price": buy_target,
        "order_class": 'bracket',
        "take_profit": {
            "limit_price": take_profit
        },
        "stop_loss": {
            "stop_price": stop_loss,
            "limit_price": stop_loss,
        }
    }

    return json.dumps(data)


def connect_to_endpoint(url, headers, data):
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        print(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()


def submit_order(ticker, side, notional, buy_target, take_profit, stop_loss):
    print("Buying ~${} of {} at {}, with take profit {} and stop loss {}\n".format(
        notional, ticker, buy_target, take_profit, stop_loss))
    url = create_url()
    headers = create_headers()
    data = create_data(ticker, side, notional,
                       buy_target, take_profit, stop_loss)
    json_response = connect_to_endpoint(url, headers, data)
    return json_response


def get_all_orders():
    url = create_url()
    headers = create_headers()
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()


def cancel_order(order_id):
    url = create_url() + "/" + order_id
    headers = create_headers()
    response = requests.delete(url, headers=headers)
    if response.status_code != 204:
        print(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )


def modify_order(order_id, ticker, side, notional, buy_target, take_profit, stop_loss):
    cancel_order(order_id)
    submit_order(ticker, side, notional, buy_target,
                 take_profit, stop_loss)


def get_order_id(ticker):
    orders_list = get_all_orders()
    for o in orders_list:
        symbol = o["symbol"]
        if ticker == symbol:
            order_id = o["id"]
            return order_id
    return None
