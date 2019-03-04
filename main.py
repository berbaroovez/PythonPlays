import socket
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import config
server ='irc.chat.twitch.tv'
port = 6667
nickname = 'pythonplaystwitch'

channel='#pythonplaystwitch'
message =""
#connects to twitch irc
sock = socket.socket()
sock.connect((server, port))
sock.send(f"PASS {config.token}\r\n".encode('utf-8'))
sock.send(f"NICK {nickname}\r\n".encode('utf-8'))
sock.send(f"JOIN {channel}\r\n".encode('utf-8'))


#opens up website
global driver
driver = webdriver.Chrome()

driver.get("https://www.topofthespots.com")


playButton = driver.find_element_by_class_name("game-screen__start-game")
playButton.click()


def topSpot():
    global message
    global driver


    def sendMessage(sock, message):
        """
        This function connects to the twitch irc and used the PRIVMSG to send a message to the twitch chat.
        """
        messageTemp = "PRIVMSG " + channel +" :" +message
        sock.send((messageTemp+ "\n").encode())

    def wrongChoice():
        """
        This function checks the page for tge class name is-wrong which indicates the wrong choice was made.
        When it detects the wrong choice was made it grabs the button element for restarting and clicks it
        """
        highScoreCheck=''
        updateHighScore=''
        print("Checking if the correct choice was made......")
        time.sleep(5)
        isWrong = driver.find_elements_by_class_name("is-wrong")

        if len(isWrong) > 0:
            print("Wrong choice was made")
            score = driver.find_element_by_class_name("game-over-screen__score").text
            highScoreCheck = open("highscore.txt", "r")

            # if int(score) > int(highScoreCheck.read()):
            #     print("A New High Score!")
            #     updateHighScore = open("highscore.txt", "w")
            #     updateHighScore.write(score)



            #This was done because i was getting an error about not being able to interact with button
            element = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, "game-over-screen__play-again")))
            element.click()

        else:
            print("Correct choice!")

    def timer():
        """
        This function is the timer that runs while votes are collected. Timerlength can be changed to increase or decease the time for colleting votes.
        While the time is running the programs takes in the messages and counts how many say one or two.
        After the timer runs out a choice is made depending on which choice had more votes. If tied the timer starts again


        #---------Note
        a message from the channel that is something like: onetwoone will be counted towards one. Also a message like: TWOTWOone will be
        counted as one as well.
        :return:
        """
        global message
        oneCounter = 0
        twoCounter = 0
        timerLength = time.time()+7

        while time.time() < timerLength:

            if "one" in message.lower():
                oneCounter += 1
                message = ""
            elif "two" in message.lower():
                twoCounter += 1
                message = ""
            else:
                pass

        if oneCounter > twoCounter:
            selectorButton = driver.find_elements_by_class_name("playfield-pane")
            print("first choice")
            # have to use arguments because another element is blocking the button
            driver.execute_script("arguments[0].click();", selectorButton[1])

            wrongChoice()
        elif twoCounter > oneCounter:
            selectorButton = driver.find_elements_by_class_name("playfield-pane")

            # have to use arguments because another element is blocking the button
            driver.execute_script("arguments[0].click();", selectorButton[2])
            print("2nd Choice")

            wrongChoice()
        else:
            pass

        print("------------------------")
        print("ONE: " , oneCounter)
        print("TWO: ", twoCounter)
        print("------------------------")

    while True:
       sendMessage(sock, "Timer has started...Place your votes")
       timer()
       #sendMessage(sock, "Sleeping for 15 seconds to avoid incorrect votes!")
       #time.sleep(15)






def twitchChat():
    """
    The funtion runs all things concerned with connectign to twitch and receiving the chat messages
    """
    def joinchat():
        """
        This function first tries to join the chat by recieving the standard protocol messages that twitch sends to a irc client
        This sends all messages to the laodingComplete function to see if the correct message has confirmed the connection
        :return:
        """
        Loading = True
        while Loading:
            readbuffer_join = sock.recv(1024).decode()
            for line in readbuffer_join.split("\n")[0:-1]:
                print(line)
                Loading = loadingComplete(line)

    def loadingComplete(line):
        """
        This function takes messages one at a time to see if they include the line End of Names list which confirms the bot is connected to the channel
        Once connceted the bot sends a message to confirm its in the chat room

        :param Line is a message by message stream of the twitch chat
        :return:
        """

        if("End of /NAMES list" in line):
            print("Bot has joined " + channel +"'s channel")
            sendMessage(sock, "Chat room is popping")
            return False
        else:
            return True

    def sendMessage(sock, message):
        messageTemp = "PRIVMSG " + channel +" :" +message
        sock.send((messageTemp+ "\n").encode())

    def getUser(line):
        """
        This parses a message that is received by the bot that contains lots of information into just the username
        :param line:
        :return:
        """
        seperate = line.split(":", 2)
        user = seperate[1].split("!",1)[0]
        return user

    def getMessage(line):
        """
        This parses the incoming data from line to get just the chat message
        :param Line is a message by message stream of the twitch chat
        :return:
        """
        global message
        try:
            message = (line.split(":",2))[2]
        except:
            message=""
        return message

    def Console(line):
        if "PRIVMSG" in line:
            return False
        else:
            return True
    joinchat()


    while True:
        try:
            readbuffer = sock.recv(1024).decode()
        except:
            readbuffer =""

        for line in readbuffer.split("\r\n"):
            if line == "":
                pass
            elif "PING" in line and Console(line):
                pongMSG = "PONG tmi.chat.twitch.tv\r\n".encode()
                sock.send(pongMSG)
                print(pongMSG)
                continue
            else:
                user = getUser(line)
                messagePrint = getMessage(line)

                print(user+": " +messagePrint)


if __name__ == '__main__':
    """
    Multi threading was used to run both main functions at the same time. 
    """
    t1 = threading.Thread(target=twitchChat)
    t1.start()
    t2 = threading.Thread(target=topSpot)
    t2.start()
    print("main")
