import json

import functions
import os, datetime, pprint

pp = pprint.pprint

year = datetime.datetime.now().year
year = 2019
day_zero = datetime.datetime(year - 5, 1, 1, 0)
day_one = datetime.datetime(year, 1, 1, 0)
day_end = datetime.datetime(year + 1, 1, 1, 0)

start_time = day_one.timestamp()
end_time = day_end.timestamp()

user = "melody"

cessions = []
cessions_raw = []

balances = {

}
sleep = 4

trades = functions.query_all_kraken("TradesHistory", "trades", user, day_zero, sleep)
ledgers = functions.query_all_kraken("Ledgers", "ledger", user, day_zero, sleep)
translate = {
    "212": "Balance before selling",
    "213": "Value got from selling",
    "214": "Fees",
    "215": "Value net of fees",
    "216": "Soulte",
    "217": "Value net of soulte",
    "218": "Value net of soutle and fees",
    "219": "Sum of buys since last selling",
    "220": "Total cost of buys since start",
    "221": "Previous cessions included",
    "222": "Soultes included in buys",
    "223": "Cost of buys net",
    "224": "Loss / Win cession",

}
status = {
    "212": 0,
    "213": 0,
    "214": 0,
    "215": 0,
    "216": 0,
    "217": 0,
    "218": 0,
    "219": 0,
    "220": 0,
    "221": 0,
    "222": 0,
    "223": 0,
    "224": 0,

}


def ktranslate(k):
    return f"{k}: {translate.get(k, '')}"


can_start = False
var_212_back = 0
last_cession = False

ledgers.sort(key=lambda x: x["time"])
trades.sort(key=lambda x: x["time"])

best_date = 0

for trade in trades:
    if not "EUR" in trade.get("pair"):
        continue
    for ledger in ledgers:
        if ledger["asset"] != "ZEUR" and ledger.get("time") < trade.get("time"):
            balances.setdefault(ledger["asset"], {"balance": 0})
            balance = balances.get(ledger["asset"])
            balance["balance"] = float(ledger["balance"])

    functions.update_balances_values(balances, trade, user)
    value = sum([bal.get("value_atm") for name, bal in balances.items() if bal.get("value_atm")])

    if value < 25 and trade.get("time") < start_time:
        best_date = trade.get("time")
balances = {}

current_trade = {}


def merge_trade(partial_trade):
    global current_trade
    current_trade.update({
        "cost": float(current_trade.get("cost")) + float(partial_trade.get("cost")),
        "fee": float(current_trade.get("fee")) + float(partial_trade.get("fee")),
        "vol": float(current_trade.get("vol")) + float(partial_trade.get("vol")),
    })
    return current_trade


def trade_group(partial_trade, trades, index):
    global current_trade
    result = False
    if not index + 1 == len(trades) and trades[index + 1].get("ordertxid") == partial_trade.get("ordertxid"):
        if not current_trade.get("trades_id"):
            current_trade = partial_trade
        else:
            merge_trade(partial_trade)
    else:
        if current_trade.get("ordertxid"):
            result = merge_trade(partial_trade)
        else:
            result = partial_trade
        current_trade = {}
    return result
    # if index+1==len(trades) or current_trade.get("trades_id")


for index, partial_trade in enumerate(trades):

    if not "EUR" in partial_trade.get("pair"):
        continue

    trade = trade_group(partial_trade, trades, index)
    # trade=partial_trade
    if not trade:
        continue
    if trade.get("time")>end_time:
        break
    for ledger in ledgers:
        if ledger["asset"] != "ZEUR" and ledger.get("time") < trade.get("time"):
            balances.setdefault(ledger["asset"], {"balance": 0})
            balance = balances.get(ledger["asset"])
            balance["balance"] = float(ledger["balance"])

    functions.update_balances_values(balances, trade, user)
    status["211"] = datetime.datetime.fromtimestamp(trade.get("time")).strftime("%d/%m/%Y, %H:%M")
    status["212"] = sum([bal.get("value_atm") for name, bal in balances.items() if bal.get("value_atm")])

    can_start = can_start or (trade["type"] == "buy" and var_212_back > 0 and trade.get("time") >= best_date)
    var_212_back = max(var_212_back, status["212"])
    if can_start and trade.get("type") == "buy":
        status["219"] += float(trade.get("cost"))
    elif can_start and trade.get("type") == "sell":
        print("SELL ", trade)
        status["220"] = status.get("219") + (last_cession[ktranslate("220")] if last_cession else 0)
        # B21+B23*B17/B12
        status["222"] = 0
        # =C21+C23*C17/C12
        status["221"] = (status["221"] + status["223"] * status["217"] / last_cession[
            ktranslate("212")]) if last_cession else 0
        status["223"] = status["220"] - status["221"] - status["222"]
        status["213"] = float(trade.get("cost"))
        status["214"] = float(trade.get("fee"))
        status["215"] = status["213"] - status["214"]
        status["216"] = 0
        status["217"] = status["213"] - status["216"]
        status["218"] = status["213"] - status["214"] - status["216"]

        status["224"] = status["218"] - status["223"] * status["217"] / status["212"]  # C18-C23*C17/C12
        status["Order ID"] = trade.get("ordertxid")
        # status["Balance"] = balances
        cessions_raw.append(status.copy())
        last_cession = {ktranslate(k): v for k, v in status.items()}
        cessions.append(last_cession)
        status["219"] = 0
functions.workbook(cessions, f"cessions.{user}.xlsx",
                   lambda x: {'bg_color': "90ee90" if x[ktranslate("224")] > 0 else "ffa07a"})

json.dump(cessions_raw, open(f"cessions.{user}.json", "w"), indent=4)
