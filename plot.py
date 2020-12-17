import datetime
import json

import random
import matplotlib.pyplot as plt
user = "thomas"
cessions = json.load(open(f"cessions.{user}.json"))

# make up some data
x = [datetime.datetime.fromtimestamp(c.get("Order TS")) for c in cessions]
y = [sum([c.get("224") for c in cessions[:idx+1]]) for idx, val in enumerate(cessions)]
y2 = [val.get("224") for idx, val in enumerate(cessions)]

# plot
plt.plot(x,y)
# beautify the x-labels
plt.gcf().autofmt_xdate()

plt.show()