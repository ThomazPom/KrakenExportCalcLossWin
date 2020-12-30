import datetime
import json
import pprint

pp = pprint.pprint

import functions

user = "thomas"
user_alt = "thomas"

year = datetime.datetime.now().year
day_zero = datetime.datetime(year - 5, 1, 1, 0)
day_end = datetime.datetime(year + 1, 1, 1, 0)

sleep = 4

trades = functions.query_all_kraken("TradesHistory", "trades", user, day_zero, sleep)
ledgers = functions.query_all_kraken("Ledgers", "ledger", user, day_zero, sleep)

balances = {

}




template = {
    "insert_date": "",
    "insert_ts": 0,
    "eb": 0,
    "tb": 0,
    "m": 0,
    "n": 0,
    "c": 0,
    "v": 0,
    "e": 0,
    "mf": 0,
    "user": "",
    "eur_balance": 0,
    "invested": 0
}

trade_balance_history = []
for trade in trades:
    if not "EUR" in trade.get("pair"):
        continue
    for ledger in ledgers:
        if ledger.get("time") < trade.get("time"):
            balances.setdefault(ledger["asset"], {"balance": 0})
            balance = balances.get(ledger["asset"])
            balance["balance"] = float(ledger["balance"])

    functions.update_balances_values(balances, trade, user)
    doc = template.copy()
    doc["insert_date"]=datetime.datetime.utcfromtimestamp(trade.get("time")).isoformat()
    doc["insert_ts"]=trade.get("time")
    doc["user"]=user_alt

    value = sum([bal.get("value_atm") for name, bal in balances.items() if bal.get("value_atm")])
    doc["invested"]=value
    doc["eb"]=doc["invested"]+balances.get("ZEUR",{"balance":0}).get("balance")
    doc["eur_balance"]=balances.get("ZEUR",{"balance":0}).get("balance")

    doc["_index"]="cryptowatch-history_of_trade_balance-"+doc["insert_date"][0:7]
    doc["_type"]="history_of_trade_balance"
    trade_balance_history.append(doc)

    #print(trade.get("type"),doc["eb"],trade)
    doc["trade_time"]=trade.get("time")
    doc["trade"]=trade
#pp(trade_balance_history)
json.dump(trade_balance_history,open(f"tradebalance.history.{user}.json","w"),indent=4)