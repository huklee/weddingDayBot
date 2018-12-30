import pickle
import sys
from weddingDayBot.weddingDayBot import *
import time

from datetime import datetime

checkMonth = ["2019", "9"]

checkList = [["9/7", "14:00"]
    ,["9/7", "14:00"]
    ,["9/8", "14:00"]
    ,["9/27", "14:00"]
    ,["9/28", "14:00"]
]

def run(slackToken, showAll=False):
    global checkMonth, checkList, dateIndexMap 
    
    # Run the agent
    driver = getWeddingDayDriver()

    checkNewPosts(driver, checkMonth, checkList, slackToken, showAll)
    driver.quit()
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage : python main.py [slackbotToken] [showAllCheck]")
        exit()

    # show option for ShowAll
    if len(sys.argv) >= 3 and sys.argv[2] == "Y":
        showAll = True
    else:
        showAll = False

    # showAll when the start of the day
    h, m = datetime.now().hour, datetime.now().minute
    if h == 7 and m == 0:
        showAll = True

    run(sys.argv[1], showAll)
    sendSlackMsgSimple(sys.argv[1], "#test", "CHECKED "+time.strftime("%Y-%m-%d %l:%M%p %Z"))                                                                                                                   
