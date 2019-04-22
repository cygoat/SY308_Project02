#!/usr/bin/python3

import config
import socket
import select
import sys

class router:

  def __init__(self):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.s.bind((config.local_ip, config.port_router))

  def __del__(self):
    self.s.close()

  def sendBytesToBank(self, m):
    self.s.sendto(m, (config.local_ip, config.port_bank))

  def sendBytesToATM(self, m):
    self.s.sendto(m, (config.local_ip, config.port_atm))

  def recvBytes(self):
      data, addr = self.s.recvfrom(config.buf_size)
      return addr[0], addr[1], data

  #===============================================================
  # Handle incoming data
  #===============================================================
  def handleData(self, data, port):
    if port == config.port_atm:
      #print("Received from atm:", data.decode())
      self.sendBytesToBank(data)
    else:
      #print("Received from bank:", data.decode())
      self.sendBytesToATM(data)


  def mainLoop(self):
    while True:
      l_socks = [sys.stdin, self.s]

      # Get the list sockets which are readable
      r_socks, w_socks, e_socks = select.select(l_socks, [], [])

      for s in r_socks:
        # Incoming data from the router
        if s == self.s:
          ip, port, data = self.recvBytes()
          if ip == config.local_ip:
            self.handleData(data, port) # call handleRequest

        # User entered a message
        else:
          m = sys.stdin.readline().rstrip("\n")
          if m == "quit":
            return


if __name__ == "__main__":
  rt = router()
  rt.mainLoop()
