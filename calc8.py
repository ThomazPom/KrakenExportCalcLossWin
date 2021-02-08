import datetime

import json

import functions

user = "thomas"
user_alt = "thomas"

year = 2021
day_one = datetime.datetime(year, 1, 1, 0, tzinfo=datetime.timezone.utc)
day_end = datetime.datetime(year + 1, 1, 1, 0, tzinfo=datetime.timezone.utc)
try_adjust_when_no_data = True
sleep = 5
# my timestamps are gmt .. insert dates are utc

last_ledgers = functions.query_all_kraken("Ledgers", "ledger", user, day_one, 0, end_day=day_end, crawl_to=10,
                                          use_cache=False)

offsetmax = last_ledgers.get("meta").get("set_size") - 10

fisrt_ledgers = functions.query_all_kraken("Ledgers", "ledger", user, day_one, 0, end_day=day_end, offset=offsetmax,
                                           use_cache=False)

first_ledger_dt = datetime.datetime.utcfromtimestamp(fisrt_ledgers["items"][0].get("time")).isoformat()

best_date_doc = functions.search_tradebal("*-history_of_trade_balance-*",
                                          [{"match": {"user": user_alt}},
                                           {"range": {"insert_date": {"lte": first_ledger_dt}}},
                                           {"range": {"invested": {"lte": 30}}}])

print(first_ledger_dt)
print(best_date_doc.get("insert_date"))
best_date_dt = datetime.datetime.fromisoformat(best_date_doc.get("insert_date"))
print(best_date_dt)

ledgers = functions.query_all_kraken("Ledgers", "ledger", user, best_date_dt, 4, end_day=day_end, use_cache=True).get(
    "items")

trades_dict = {

}

for index, ledger in enumerate(ledgers):
    trades_dict.setdefault(ledger.get("refid"), {})
    trade = trades_dict.get(ledger.get("refid"))
    trade["trades_id"] = ledger.get("refid")
    trade["time"] = ledger.get("time")
    if ledger.get("asset") == "ZEUR":
        trade["cost"] = abs(float(ledger.get("amount")))
        trade["fee"] = ledger["fee"]
        trade["pair"] = trade.get("pair", "") + "ZEUR"
        trade["type"] = "buy" if float(ledger.get("amount")) < 0 else "sell"
    else:
        trade["pair"] = ledger.get("asset") + trade.get("pair", "")
        trade["vol"] = abs(float(ledger.get("amount")))

    trade["ordertxid"] = str(index)

# prefer use data from api

ledgers = functions.query_all_kraken("Ledgers", "ledger", user, best_date_dt, sleep, end_day=day_end,
                                     use_cache=True).get(
    "items")

trades_alones = functions.query_all_kraken("TradesHistory", "trades", user, best_date_dt, sleep, end_day=day_end,
                                           use_cache=True).get("items")
for trade in trades_alones:
    trades_dict[trade["trades_id"]] = trade

trades = list(trades_dict.values())
trades.sort(key=lambda x: x["time"])
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


last_cession = False

cessions_raw = []

cessions = []

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


for index, partial_trade in enumerate(trades):
    if not "EUR" in partial_trade.get("pair"):
        continue
    if "ZEUR" == partial_trade.get("pair"):
        continue
    trade = trade_group(partial_trade, trades, index)
    # trade=partial_trade
    if not trade:
        continue

    status["211"] = datetime.datetime.fromtimestamp(trade.get("time")).strftime("%d/%m/%Y, %H:%M")
    best_212_doc = functions.search_tradebal("*-history_of_trade_balance-*",
                                             [{"match": {"user": user_alt}},
                                              {"range": {"insert_date": {"lte": datetime.datetime.utcfromtimestamp(
                                                  trade.get("time")).isoformat()}}},
                                              ])

    status["212"] = best_212_doc.get("invested")
    if trade.get("type") == "buy" and trade.get("time") >= best_date_dt.timestamp():
        status["219"] += float(trade.get("cost"))
    elif trade.get("type") == "sell" and trade.get("time") >= best_date_dt.timestamp():

        print("SELL ", trade)
        status["220"] = status.get("219") + (last_cession[ktranslate("220")] if last_cession else 0)
        # B21+B23*B17/B12
        status["222"] = 0
        # =C21+C23*C17/C12
        status["221"] = (status["221"] + status["223"] * status["217"] / last_cession[
            ktranslate("212")]) if last_cession else 0
        status["223"] = status["220"] - status["221"] - status["222"]
        status["213"] = float(trade.get("cost"))
        if status["213"] > status["212"] and try_adjust_when_no_data:
            status["212"] += status["213"]
        status["214"] = float(trade.get("fee"))
        status["215"] = status["213"] - status["214"]
        status["216"] = 0
        status["217"] = status["213"] - status["216"]
        status["218"] = status["213"] - status["214"] - status["216"]

        status["224"] = status["218"] - status["223"] * status["217"] / status["212"]  # C18-C23*C17/C12
        status["pair"] = trade.get("pair")
        status["vol"] = trade.get("vol")
        status["Order ID"] = trade.get("ordertxid")
        status["Order TS"] = trade.get("time")
        # status["Balance"] = balances
        cessions_raw.append(status.copy())
        last_cession = {ktranslate(k): v for k, v in status.items()}
        cessions.append(last_cession)
        status["219"] = 0

json.dump(cessions_raw, open(f"cessions.{user}.json", "w"), indent=4)

functions.workbook(cessions, f"cessions.{user}.xlsx",
                   lambda x: {'bg_color': "90ee90" if x[ktranslate("224")] > 0 else "ffa07a"})
