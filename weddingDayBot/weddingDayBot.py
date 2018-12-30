import re
import time
import platform 
from selenium import webdriver
from slacker import Slacker
from bs4 import BeautifulSoup 

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
       
dateIndexMap = {"11:00":1, "14:00":2, "17:00":3}
channel = "wedding"

if "armv7" in platform.platform():
    isRPi = True
    from pyvirtualdisplay import Display
else:
    isRPi = False

def getWeddingDayDriver():
    global isRPi

    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "none"

    chrome_options = webdriver.ChromeOptions() 
    chrome_options.add_argument('--no-sandbox') 
    chrome_options.add_argument('--window-size=1420,1080') 
    chrome_options.add_argument('--headless') 
    chrome_options.add_argument('--disable-gpu')

    driver = webdriver.Chrome("/home/huklee/Downloads/chromedriver", desired_capabilities=caps, chrome_options = chrome_options)

    return driver

# Return new Posts from the boardTail
def getNewPosts(driver, checkMonth):
    # 1. load the initial page
    year, month = checkMonth[0], checkMonth[1]
    driver.get("https://eng.snu.ac.kr/enghouse_reserve?tab=3&year={0}&month={1}".format(year, month))

    # wait for loading components
    time.sleep(5)

    # 2.
    from selenium.webdriver.common.action_chains import ActionChains
    elem = driver.find_element_by_xpath("//input[@id='agree']")
    actions = ActionChains(driver)
    actions.click(elem).perform()
    elem = driver.find_element_by_xpath("//button[@id='enghouse_w']").click()
    actions = ActionChains(driver)
    actions.click(elem).perform() 
    
    # 3. 
    time.sleep(5)
    from bs4 import BeautifulSoup 
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    posts = soup.select("div.reserve_calendar > table")
    elems = posts[0].findAll("td") 

    return elems


"""
assume that current page is a board post page
return (authorKi, authorName)
"""
def getAuthorInfo(driver):
    # get author Name
    urlHead = "https://www.bawi.org/"
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    pasts = soup.select("#content > ul > li.author > a.user-profile")

    authorName = pasts[0].text    

    # get author Ki
    urlTail = pasts[0]["href"]
    driver.get(urlHead + urlTail)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    posts = soup.select("body > div > table > tbody > tr > td > h2 > a")
    authorKi = posts[0].text

    return (authorKi, authorName)

def init():
    pass 

def checkNewPosts(driver, checkMonth, checkList, slackToken, showAll=False):
    global dateIndexMap, channel
    newPosts = getNewPosts(driver, checkMonth)

    result = {}
    for i, e in enumerate(newPosts):
        for (date, cTime) in checkList:
            if date in e.text:
                timeIndex = dateIndexMap[cTime]
                item = newPosts[i+timeIndex].text
                result[(date, cTime)] = item
                
                print(date, cTime, item)

                # show all check
                if showAll == False and "예약완료" in item:  continue

                notifySlack(driver, channel, ["{} {}".format(date,cTime), item], slackToken)

    return result

def sendSlackMsgSimple(token, channel, pretext):
    slack = Slacker(token)
    nowTime = time.time()  # unix_time_stamp
    
    att = [{
            "pretext": pretext,
    }]
    
    slack.chat.post_message(channel, attachments=att)    

def sendSlackMsg(token, channel, pretext, title, text, color="good"):
    slack = Slacker(token)
    nowTime = time.time()  # unix_time_stamp
    
    att = [{
            "pretext": pretext,
            "title": title,
            "text": text,
            "color": color, # good(green)
            "mrkdwn_in": [
                "text",
                "pretext"
            ],

            "ts":nowTime
    }]
    
    slack.chat.post_message(channel, attachments=att)    

def notifySlack(driver, channel, posts, slackToken):
    title = posts[0]
    text = posts[1]

    # 02. send the msg through slack
    sendSlackMsg(slackToken, channel, "라쿠치나 웨딩홀 예약 업데이트", title, text)
            
