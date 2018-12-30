import re
import time
import platform 
from selenium import webdriver
from slacker import Slacker
from bs4 import BeautifulSoup 

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC

if "armv7" in platform.platform():
    isRPi = True
    from pyvirtualdisplay import Display
else:
    isRPi = False

def getBawiDriver(uid, passwd):
    global isRPi

    if isRPi == True:
        display = Display(visible=0, size=(800, 600))
        display.start()
        driver = webdriver.Firefox()
    else:
        driver = webdriver.Chrome("/Users/huklee/Work/crawling/chromedriver")    
    driver.get("http://www.bawi.org")

    wait(driver, 10).until(EC.element_to_be_clickable((By.ID, "login_id"))).send_keys(uid)
    wait(driver, 10).until(EC.element_to_be_clickable((By.ID, "login_passwd"))).send_keys(passwd)
    wait(driver, 10).until(EC.element_to_be_clickable((By.ID, "login_submit"))).click()
    return driver

# Return new Posts from the boardTail
def getNewPosts(driver, boardTail, readPostsIdSet):
    boardHead = "https://www.bawi.org/board/"

    newPosts = {}
    readPostsId = readPostsIdSet[boardTail]

    driver.get(boardHead + boardTail)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Every Title of the posts
    #   exmple of the title tag
    #   content > div.article-list.wrapper > ul:nth-child(3) > li.title > a
    posts = soup.select("div.article-list.wrapper > ul")

    
    # Post Check
    for p in posts:
        global pp
        tag = p.find("li", {"class":"title"}).find("a")
        pp = tag
        if tag is None: 
            continue

        title = tag.text
            
        for i in p.findAll("a", {"href":re.compile("tno")}):
    #         print(i)
    #         print(p.findAll("li", {"class":"read"}))
            if i.text not in readPostsId:
                readPostsId.add(i.text)
                urlTail = i["href"]
                newPosts[i.text] = (title, urlTail)
                print("[New Post]", i.text, urlTail)
    
    return newPosts


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
    boardHead = "https://www.bawi.org/board/"
    #https://www.bawi.org/board/read.cgi?bid=638&aid=1704810 boardList = {"구인/구직":"read.cgi?bid=8", "결혼":"read.cgi?bid=638"}
    boardTail = "read.cgi?bid=588"
    readPostsId = set()


def checkNewPosts(driver, boardList, readPostsIdSet, slackToken):
    assert set(boardList.values()) == set(readPostsIdSet.keys())

    boardHead = "https://www.bawi.org/board/"
        
    for key in boardList.keys():
        urlTail = boardList[key]
    
        newPosts = getNewPosts(driver, urlTail, readPostsIdSet)
        print(newPosts)
        notifySlack(driver, key, newPosts, slackToken)

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
    boardHead = "https://www.bawi.org/board/"

    for title, urlTail in posts.values():
        # 01. goto the post with the driver        
        print("[NEW POST]", urlTail)
        driver.get(boardHead + urlTail)

        # DEV...
        print(getAuthorInfo(driver))

        driver.get(boardHead + urlTail)
        html = driver.page_source

        soup = BeautifulSoup(html, "html.parser")
        content = soup.select("li.body.text > table > tbody > tr > td")
        
        for i in content[0].findAll("br"):
            i.replaceWith("\n")

        text = content[0].text
        title = ("[%s/%s]" % (getAuthorInfo(driver))) + title

        # 02. send the msg through slack
        sendSlackMsg(slackToken, channel, boardHead + urlTail, title, text)
            
