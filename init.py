import os,git
if not os.path.exists("python3-krakenex") and not os.path.exists('python3krakenex'):
    print("Git clone ..")
    git.Git("./").clone("https://github.com/veox/python3-krakenex")

if os.path.exists("python3-krakenex") and not os.path.exists('python3krakenex'):
    print("Rename")
    os.rename("./python3-krakenex", "./python3krakenex")

