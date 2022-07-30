import json
import yfinance as yf

local_config = {}
config = {}
bot = None
users = {}


def reload_config():
    global local_config
    global config
    local_config = json.loads(open(
        "local_config.json").read())  # Local config is config that should be kept different between each instance of the bot
    config = json.loads(
        open("config.json").read())


def stock_v(symbol: str):
    t = yf.Ticker(symbol)
    try:
        return t.history()['Close'].iloc[-1]
    except IndexError:
        return None
