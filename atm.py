#!/usr/bin/python3
#
# Names:        MIDN Allison Annick, USN
#               MIDN Kevin Nguyen, USN
# Course:       SY308 - Security Fundamental Principles
# Assignment:   Project02 - ATM Redesign
# Reference:    Design Document (SY308 Project 2 Design Doc)
#

import config
import socket
import select
import sys
from Crypto.Cipher import AES
from Crypto.Util import Counter
import hashlib

class atm:
  def __init__(self):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.s.bind((config.local_ip, config.port_atm))
    self.pins = {"1234": "Alice", "4321": "Bob", "1122": "Carol"}
    self.promptMessage = "ATM: "
    self.currentUser = None # If this is set, the user is authenticated

    # Set up AES CTR mode
    fdSSatm = open("ssATM.bin", "r")
    self.aesKey = fdSSatm.readline().strip()
    self._AESctr = Counter.new(128)
    self._AESKey = str.encode(self.aesKey)
    self.AES = AES.new(self._AESKey, AES.MODE_CTR, counter=self._AESctr)

  def __del__(self):
    self.s.close()

  def sendBytes(self, m):
    self.s.sendto(m, (config.local_ip, config.port_router))

  def recvBytes(self):
      data, addr = self.s.recvfrom(config.buf_size)
      if addr[0] == config.local_ip and addr[1] == config.port_router:
        return True, data
      else:
        return False, bytes(0)


  #====================================================================
  # TO DO: Modify the following function to output prompt properly
  #====================================================================
  def prompt(self):
    sys.stdout.write(self.promptMessage)
    sys.stdout.flush()


  #====================================================================
  # TO DO: Modify the following function to handle the console input
  #====================================================================
  def handleLocal(self,inString):

    # print("inString is:", inString)
    inString = inString.strip().lower()

    if inString == "begin-session":
        # Assuming user has copied the card file to [ inserted.card ]
        # and that no user is already logged in
        if self.currentUser != None:
            print("Error: You are already logged in as" + self.currentUser)
            self.prompt()
            return

        # Get the correct pin
        with open("inserted.card", 'r') as insertedCard:
            lstCardData = insertedCard.read().strip().split()
            pin = lstCardData[0]

        # Authenticate the user by asking for pin
        pinAttempt = input("Enter PIN: ")
        print("Your attempt is: ", pinAttempt)
        if pinAttempt == pin: # Correct pin was entered
            self.currentUser = self.pins[pin]
            self.promptMessage = "ATM: (" + self.currentUser + "): "
            print("Welcome, " + self.currentUser + "!")
            inString = "authenticate" + " " + self.currentUser
            self.prompt()
        else:
            print("Unauthorized: Wrong PIN")
            self.prompt()

    elif inString == "end-session":
        # assuming that someone is already logged in
        if self.currentUser == None:
            print("Error: Must be logged in to do this!")
            self.prompt()
            return

        print("Goodbye, " + self.currentUser + "!")
        inString = "deauthenticate" # clears out the current user on the bank
        self.currentUser = None
        self.promptMessage = "ATM: "
        self.prompt()

    elif self.currentUser == None: # No one logged in
        print("Error: must log in!")
        self.prompt()
        return

    self.AES = AES.new(self._AESKey, AES.MODE_CTR, counter=self._AESctr)
    encString = self.AES.encrypt(inString.encode())
    self.sendBytes(bytes(inString, "utf-8"))


  #====================================================================
  # TO DO: Modify the following function to handle the bank's reply
  #====================================================================
  def handleRemote(self, inBytes):
    self.AES = AES.new(self._AESKey, AES.MODE_CTR, counter=self._AESctr)
    decInput = self.AES.decrypt(inBytes)
    print(decInput.decode("utf-8"))
    self.prompt()


  def mainLoop(self):
    self.prompt()

    while True:
      l_socks = [sys.stdin, self.s]

      # Get the list sockets which are readable
      r_socks, w_socks, e_socks = select.select(l_socks, [], [])

      for s in r_socks:
        # Incoming data from the router
        if s == self.s:
          ret, data = self.recvBytes()
          if ret == True:
            self.handleRemote(data) # call handleRemote


        # User entered a message
        elif s == sys.stdin:
          m = sys.stdin.readline().rstrip("\n")
          if m == "quit":
            return
          self.handleLocal(m) # call handleLocal


if __name__ == "__main__":
  a = atm()
  a.mainLoop()
