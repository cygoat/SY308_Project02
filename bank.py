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

class bank:
  def __init__(self):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.s.bind((config.local_ip, config.port_bank))

    self._username = 0
    self._pin = 1
    self._balance = 2

    self._alice = 0
    self._bob = 1
    self._carol = 2


    # Read data from ssBank.bin
    ssBank = open("ssBank.bin","r")
    self.lstUserData = []
    lstUsers = ssBank.readlines()
    self.aesKey = lstUsers[0].strip()
    del lstUsers[0]
    for user in lstUsers:
        lstInfo = user.strip().split(";")
        self.lstUserData.append(lstInfo)

    # Dict to keep track of all users and balances
    self.accounts = {"alice": 123, "bob": 456, "carol": 789}

    # Current user logged into the atm
    self.currentUser = ""

    # AES CTR setup
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

  def readUser(self, user):
      # Arguments: a string $user that specifies which card to open
      # Returns:   a list lstData that contains information about user
      #            [ $cardName, $pin]

      # Open card file
      card = user + ".card"
      while True:
          try:
              # Read card data
              fdUserCard = open(card, 'r')
              lstData = fdUserCard.read().strip().split(" ")

              pin = lstData[0]

              userData = [user, pin]
              break
          except FileNotFoundError:
              return 2 # Errno 2 for user not existing
              # self.prompt()

      fdUserCard.close()
      return userData

  def handleCommand(self, command):
      # Arguments: A list that contains the command components
      # Returns:   String (command output)
      if command is None: # empty command
          return ""
      if command[0] == "authenticate": # ATM user has just ran begin-session
          self.currentUser = command[1].lower()
          return
      if command[0] == "deauthenticate": # ATM user has just ran end-session
          self.currentUser = ""
          return
      output = "" # return value
      if command[0] == "deposit":
          # expects: deposit $user $amt
          while True:
              try:
                  if len(command) == 2: # User is logged in
                    user = self.currentUser.lower()
                    amt = int(command[1])

                  else: # No user is logged in, local bank behavior
                    user = command[1]
                    amt = int(command[2])

                  if (len(command) == 3) and (self.currentUser != ""):
                      # User should not be specifying a different user
                      print(command, "is command")
                      print("self.currentUser is", self.currentUser)
                      return "Error: Wrong arguments for an authenticated user!"

                  userData = self.readUser(user)
                  if userData == 2: # FileNotFoundError
                    print("Error, card attempted access was", user)
                    return "Error: Cannot find card!"
                  currentBalance = self.accounts[userData[0]]
                  newBalance = currentBalance + amt

                  self.accounts[userData[0]] = newBalance
                  user = user.title()
                  output = "Deposited " + str(amt) + " to " + user + "'s account"
                  return output

                  break
              except IndexError:
                  print("Error: must input user and amount to deposit.")
              except FileNotFoundError:
                  return "Error: User does not exist!"
              except ValueError:
                  return "Error: Improper format for deposit!\n\tUsage: deposit [user] [amount]"

      elif command[0] == "balance":
          if (len(command) == 1) and (self.currentUser != ""): # user is authenticated
              return "Balance is: " + str(self.accounts[self.currentUser])

          if len(command) != 2:
              return "Error: Incorrect arguments for balance!"

          if (len(command) == 2) and (self.currentUser != ""):
              # User should not be specifying a different user
              return "Error: Wrong arguments for an authenticated user!"

          user = command[1]
          currentUserData = self.readUser(user)
          if currentUserData == 2: # FileNotFoundError
            return "Error: User does not exist!"
          output = "Balance is: " + str(self.accounts[user])
          return output

      elif command[0] == "begin-session" or command[0] == "end-session":
          return None # Bank does not need to respond

      elif command[0] == "withdraw":
          while True:
              try:
                  if len(command) == 2: # User is logged in
                    user = self.currentUser.lower()
                    amt = int(command[1])

                  else: # No user is logged in, local bank behavior
                    user = command[1]
                    amt = int(command[2])

                  if (len(command) == 3) and (self.currentUser != ""):
                    # User should not be specifying a different user
                    print(command, "is command")
                    print("self.currentUser is", self.currentUser)
                    return "Error: Wrong arguments for an authenticated user!"

                  userData = self.readUser(user)
                  if userData == 2: # FileNotFoundError
                    return "Error: User does not exist!"

                  if amt < 0: # Cannot withdraw negative amount
                    return "Error: Withdrawal amount must be a positive number"
                  currentBalance = self.accounts[userData[0]]
                  newBalance = int(currentBalance) - amt
                  if newBalance < 0:
                      return ("Error: Insufficient Funds!")
                  self.accounts[userData[0]] = newBalance
                  user = user.title()
                  output = "Withdrew " + str(amt) + " from " + user +"'s account"
                  return output

                  break
              except IndexError:
                  return "Error: must input user and amount to withdraw."
              except FileNotFoundError:
                  return "Error: User does not exist!"
              except ValueError:
                  return "Error: Improper format for withdraw!\n\tUsage: deposit [user] [amount]"
              except:
                  return "Error: Bank Error!"
      else: # Command not recognized
        return "Error: Command not recognized!"


  #====================================================================
  # TO DO: Modify the following function to output prompt properly
  #====================================================================
  def prompt(self):
    sys.stdout.write("BANK: ")
    sys.stdout.flush()

  #====================================================================
  # TO DO: Modify the following function to handle the console input
  #====================================================================

  def handleLocal(self,inString):
    if inString is "":
        self.prompt()
    else:
        commandInput = inString.lower()
        command = commandInput.lower().strip().split(" ")

        output = self.handleCommand(command)
        print(output)

        self.prompt()

  #====================================================================
  # TO DO: Modify the following function to handle the atm request
  #====================================================================
  def handleRemote(self, inBytes):
    self.AES = AES.new(self._AESKey, AES.MODE_CTR, counter=self._AESctr)
    decInput = self.AES.decrypt(inBytes)
    print(decInput)
    atmCommand = decInput

    commandOutput = self.handleCommand(atmCommand.strip().split())

    while True:
        try:
            # Before sending bytes. encrypt
            self.AES = AES.new(self._AESKey, AES.MODE_CTR, counter=self._AESctr)
            encCommandOutput = self.AES.encrypt(commandOutput.encode())

            self.sendBytes(encCommandOutput.encode()) #encode the message as bytes
            break
        except AttributeError: # NoneType trying to be sent, ignore
            break
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
  b = bank()
  b.mainLoop()
