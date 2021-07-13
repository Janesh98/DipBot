import websocket
from time import sleep
import datetime
import json
import threading
import time
import os
from dotenv import load_dotenv
from alpaca import submit_order, get_all_orders, cancel_order

load_dotenv()

channel_id = os.environ['DISCORD_CHANNEL_ID']
token = os.environ['DISCORD_TOKEN']


def send_json_request(ws, request):
    ws.send(json.dumps(request))


def recieve_json_response(ws):
    response = ws.recv()
    if response:
        return json.loads(response)


def heartbeat(interval, ws):
    print('Heartbeat begin')
    while True:
        time.sleep(interval)
        heartbeatJSON = {
            "op": 1,
            "d": "null"
        }
        send_json_request(ws, heartbeatJSON)
        print("Heartbeat sent")


def save_event(data):
    with open("./data/data.json", 'r+') as file:
        file_data = json.load(file)
        file_data["alerts"].append(data)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent=4)


def analyse(event):
    try:
        order = event['d']['content'].split('\n')
        action = order[0].lower()
        if "new trade alert for" in action:
            ticker = action.split(" ")[-1].upper()
            buy_target = float(order[3].split(" ")[-1][1:])
            take_profit = float(order[2].split(" ")[-1][1:])
            stop_loss = float(order[4].split(" ")[-1][1:])
            submit_order(ticker, "buy", 1000.0, buy_target, take_profit, stop_loss)
        elif "cancelled trade for" in action:
            ticker = action.split(" ")[-1].upper()
            orders_list = get_all_orders()
            for o in orders_list:
                symbol = o["symbol"]
                if ticker == symbol:
                    print(f"Cancelling order for {ticker}")
                    order_id = o["id"]
                    cancel_order(order_id)
            print()
    except Exception:
        pass


def main():
    ws = websocket.WebSocket()
    ws.connect('wss://gateway.discord.gg/?v=9&encording=json')
    event = recieve_json_response(ws)

    heartbeat_interval = event['d']['heartbeat_interval'] / 1000
    threading._start_new_thread(heartbeat, (heartbeat_interval, ws))

    payload = {
        'op': 2,
        "d": {
            "token": token,
            "properties": {
                "$os": "linux",
                "$browser": "chrome",
                "$device": 'pc'
            }
        }
    }
    send_json_request(ws, payload)

    while True:
        event = recieve_json_response(ws)

        try:
            if event['d']['channel_id'] != channel_id:
                continue

            analyse(event)

            if isMarketClosed():
                print("Market is closed.")
                break

            # print(
            #     f"{event['d']['author']['username']}: {event['d']['content']}")
            # op_code = event('op')
            # if op_code == 11:
            #     print('heartbeat received')
        except Exception as e:
            # print(f"Error: {e}")
            pass

    ws.close()
    print("Exiting...")

# Wait for market to open.
def awaitMarketOpen():
    isOpen = datetime.datetime.utcnow().time() >= datetime.time(13, 30, 0)
    if(not isOpen):
        marketOpen = datetime.datetime.utcnow().replace(hour=13, minute=30, second=0)
        timeToOpen = marketOpen - datetime.datetime.utcnow()
        print("time until market open: {}".format(timeToOpen))
        print("Sleeping until market open...")
        sleep(timeToOpen.total_seconds())
        print("Market now open")


def isMarketClosed():
    return datetime.datetime.utcnow().time() >= datetime.time(20, 0, 0)


if __name__ == "__main__":
    awaitMarketOpen()
    main()
    # Test Mode Below with pre saved data
    # with open('./data/data.json', 'r') as f:
    #     data = json.load(f)
    # for line in data["alerts"]:
    #     analyse(line)
