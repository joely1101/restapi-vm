#!/usr/bin/python3
message=[]
def log(msg):
    message.append(msg)
    print(f"logging {message}")
  
def logClear():
    print("clear")
    message.clear()

def logGet():
    print(f"get {message}")
    if len(message) == 0:
        message.append("No message")
    newm=list(message)
    message.clear()
    
    return newm
