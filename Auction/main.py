"""
Databases - 
1. item_db = {item_id, item_name, bid_port}
"""

import socket
from threading import Thread,Lock
import time
import sys
import datetime
import os
from .models import Item
from . import db

# app = create_app()
# app.app_context().push()

mutex_m1 = Lock()
bufferSize = 1024

"""
client_zerobidder() - used to send a zero amount bid to server in case 
the timer of an item expires.
Arguments - None
Return - None
"""
def client_zerobidder(ip, port):
	serverAddressPort = (ip, port)
	# Create a UDP socket at client side
	UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	# Send to server using created UDP socket
	msg = "0;0"
	UDPClientSocket.sendto(msg.encode(), serverAddressPort)

"""
client_buyer() - function used to place a bid for a particular item
Arguments - 1. ip = ip address
            2. id = item id
            3. buyer_id = customer id
            4. bid_amt = bidding amount
Return - message denoting either bid is placed or not
"""
def client_buyer(ip, id, buyer_id, bid_amt):
	print("Following list of items (item id, item name) available for bidding)")
	item = Item.query.get(id)
	print(str(id) +' '+ item.item_name)
	port = item.port
	serverAddressPort = (ip, port)
	# Create a UDP socket at client side
	UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	# Send to server using created UDP socket
	msg = str(buyer_id) + ";" + str(bid_amt)
	# print(ip, port, id, bid_amt)
	UDPClientSocket.sendto(msg.encode(), serverAddressPort)
	msg = UDPClientSocket.recvfrom(bufferSize)
	message = msg[0].decode()
	address = msg[1]
	# print(message)
	try:
		new_bid = int(message)
		curr_bid = str(buyer_id) + ";" + str(message)
		# print(curr_bid)
		return curr_bid
	except:
		return message
	
	# l = list(map(str, message.split(';')))
	# if l[0] == "bid completed":
	# 	print("Bid Completed")
		
"""
 client_seller() - function used to open an item bidding request to the 
 UDP Server with the informations collected.
 Arguments - 1. ip - ip address
             2. port - port in which UDP Server is running
             3. id - item id
             4. seller_id - client id that generated the request
Return - final bid amount if any user placed a bid
"""
def client_seller(ip, port, id, seller_id):
	serverAddressPort = (ip, port)
	item = Item.query.get(id)
	item_name = item.item_name
	item_des = item.description
	duration = item.duration
	start_bid = item.start_bid
	msg = str(id) + ";" + item_name + ";" + item_des + ";" + duration.strftime('%H:%M:%S') + ";" + str(start_bid)
	# Create a UDP socket at client side
	UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	# Send to server using created UDP socket
	UDPClientSocket.sendto(msg.encode(), serverAddressPort)
	#after finishing the bid for that item messag recieved from UDP Server
	msgFromServer = UDPClientSocket.recvfrom(bufferSize)
	message = msgFromServer[0].decode()
	address = msgFromServer[1]
	
	#mutex m1 used to modify contents of wallet log as the bid amount is required to be added to wallet
	mutex_m1.acquire()
	try:
		with open('server_msg.txt', 'r') as f:
			temp_msgs = f.readlines()
	except:
		temp_msgs = ''
	with open('server_msg.txt', 'a') as f:
		msgs = message.split('\n')
		prod_name = msgs[0]
		if msgs[1]:
			final_bid = msgs[1]
			bidder_id = msgs[2]
		else:
			final_bid = ''
			bidder_id = ''

		if len(temp_msgs) == 0:
			msg = str(id) + ',' + bidder_id + ',' + final_bid
		else:
			msg = '\n' + str(id) + ',' + bidder_id + ',' + final_bid
		f.write(msg)

	#if there is a bid from any user then we update the amount to seller wallet
	if final_bid:
		with open('wallet.log', 'r') as f:
			all_wlts = f.readlines()
			all_wlts_dict = {}
			for wallet in all_wlts:
				w = list(map(int, wallet.split(',')))
				all_wlts_dict[w[0]] = w[1]

			prev_amt = all_wlts_dict[seller_id]
			all_wlts_dict[seller_id] = prev_amt + int(final_bid)
			all_wlts = ''
			for key, value in all_wlts_dict.items():
				all_wlts += str(key) + ',' + str(value) + '\n'
			all_wlts = all_wlts[:-1]

		with open('wallet.log', 'w') as f:
			f.writelines(all_wlts)
	mutex_m1.release()

"""
server_item_bid_thread() - used to update wallet content if a valid request is placed
from a buyer client.
Argumets - 1. bid_description - dictionary having the entire details of the bid
Return - None
"""
def server_item_bid_thread(bid_description):
	#extracting information from a client buyer
	l = list(map(str, bid_description["message"].split(';')))
	bid_amt = int(l[1])
	mutex_m2 = bid_description["lock"]  #mutex m2 used to synchronize the bidding for an item
	UDPServerSocket = bid_description["UDP_server_sock"]  #socket for sending message to client
	address = bid_description["client_addr"]  #clinet address
	mutex_m2.acquire()
	try:
		if bid_description["current_bid_amt"] <= bid_amt:  #if a bid is valid bid
			mutex_m1.acquire()  #mutex m1 is used for updating values in the wallet
			with open('wallet.log', 'r') as f:
				try:
					all_wlts_dict = {}
					all_wlts = f.readlines()
					for wallet in all_wlts:
						w = list(map(int, wallet.split(',')))
						all_wlts_dict[w[0]] = w[1]

					curr_bidder_amt = all_wlts_dict[int(l[0])]
					if bid_description['bidder_id'] == 'NA':  #if it is the first client request for the item
						all_wlts_dict[int(l[0])] = curr_bidder_amt - bid_amt
					elif bid_description["bidder_id"] == int(l[0]):  #if same client already bid for the item and was the highest bidder
						all_wlts_dict[int(l[0])] = curr_bidder_amt - (bid_amt - bid_description["current_bid_amt"] + 1)
					else:  #if some other client was the highest bidder
						prev_bidder_amt = all_wlts_dict[bid_description["bidder_id"]]
						all_wlts_dict[bid_description["bidder_id"]] = prev_bidder_amt + (bid_description["current_bid_amt"] - 1)
						all_wlts_dict[int(l[0])] = curr_bidder_amt - bid_amt
				finally:
					all_wlts = ''
					for key, value in all_wlts_dict.items():
						all_wlts += str(key) + ',' + str(value) + '\n'
					all_wlts = all_wlts[:-1]

					with open('wallet.log', 'w') as f:   #updating the entries of the wallet
						f.writelines(all_wlts)
					mutex_m1.release()

			bid_description["bidder_id"] = int(l[0])  #updating new entries
			bid_description["winning_bid"] = bid_amt
			bid_description["current_bid_amt"] = bid_amt + 1

			msg = str(bid_description["current_bid_amt"])
			UDPServerSocket.sendto(msg.encode(), address)
		else:
			msg = "failure;" + str(bid_description["current_bid_amt"])
			UDPServerSocket.sendto(msg.encode(), address)
	finally:
		mutex_m2.release()

"""
server_item_thread()- used for simulating a bidding for an item using threading to 
validate a bid and updating the wallets and item bidding informations.
Arguments - 1. item_description - dictionary containing informations regarding the item 
Return - None
"""
def server_item_thread(item_description):
	print("New Item bidding " + item_description["prod_name"])
	customer_bid = []  #for keeping a track of customers that bid for the item
	initial_bid = item_description["start_bid"]
	bid_id = "NA"
	mutex_m2 = Lock()  #defining a mutex for this item
	arg_dict = {}
	UDPServerSocket = item_description["UDP_server_sock"]
	UDPServeritemSocket = item_description["UDP_item_sock"]
	#for sending information to bid validation threads using arg_dict
	arg_dict["lock"] = mutex_m2
	arg_dict["current_bid_amt"] = initial_bid
	arg_dict["winning_bid"] = "NA"
	arg_dict["bidder_id"] = "NA"
	arg_dict["UDP_server_sock"] = UDPServeritemSocket
	time_end = time.time() + item_description["auc_time"]  #specifying the end time
	#creating a child process to call the zero_bidder and end the bidding
	pid = os.fork()
	if pid > 0:  #parent server
		item_bid_thread = []
		while time.time() < time_end:  #specifying the time interval for which requests are to considered
			msg_addr = UDPServeritemSocket.recvfrom(bufferSize)
			message = msg_addr[0].decode()
			address = msg_addr[1]
			if address not in customer_bid:
				customer_bid.append(address)
			if time.time() >= time_end:  #checking if time if request comes within time interval
				break
			arg_dict["client_addr"] = address
			arg_dict["message"] = message
			t = Thread(target=server_item_bid_thread, args = (arg_dict,))  #thread to validate bid
			item_bid_thread.append(t)
			t.start()
		for t in item_bid_thread:  #after completing biddibg joining all the threads
			t.join()
		item_description["final_bid"] = arg_dict["winning_bid"]  #updating entries to be sent to server
		item_description["bidder_id"] = arg_dict["bidder_id"]
		msg = "bid completed;highest_bidder=" + str(arg_dict["winning_bid"])
		for addr in customer_bid:
			UDPServeritemSocket.sendto(msg.encode(), addr)  #sending each client with the bidding completion information
		# msg_to_send = "Bidding completed for " + item_description["prod_name"]
		msg_to_send = item_description["prod_name"]
		if item_description["final_bid"] == "NA":
			# msg_to_send += "\nSorry, No bid placed"
			msg_to_send += "\n"
		else:
			# msg_to_send += "\nReceived " + str(item_description["final_bid"]) + " from " + str(item_description["bidder_id"])
			msg_to_send += "\n" + str(item_description["final_bid"]) + "\n" + str(item_description["bidder_id"])
		# Sending a reply to client
		UDPServerSocket.sendto(msg_to_send.encode(), item_description["cli_addr"])
	else:  #child server
		while time.time() < time_end:
			pass
		client_zerobidder('127.0.0.1', item_description["port"])  #for a zero_bid to end the bidding

"""
server() - used for accepting requests from clinet and creates a thread to start bidding for an item.
Arguments - 1. ip - ip address in which UDP server will run
            2. port - port in which to create a socket
Return - None
"""
def server(ip, port):
	#creating a socket
	socket_addr = (ip, port)
	UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	#binding the socket
	UDPServerSocket.bind(socket_addr)
	print("UDP server listening for requests")
	#msg_to_send = "Bid accepted"
	#maintaining a new port for each item bidding
	port_available = port + 1
	while(True):
		#reciece a request from client
		msg_addr = UDPServerSocket.recvfrom(bufferSize)
		message = msg_addr[0].decode()
		address = msg_addr[1]
		#extracting information from client request
		l = list(map(str, message.split(';')))
		d = {}
		d["id"] = int(l[0])
		d["prod_name"] = l[1]
		d["description"] = l[2]
		times = list(map(int, l[3].split(':')))
		# if no time has been mentioned default 5 hours
		if l[3] == "Default":
			d["auc_time"] = 5 * 60 * 60     #d["auc_time"] has the auction time in seconds
		else:
			d["auc_time"] = times[0] * 60 * 60 + times[1] * 60 + times[2]
		d["start_bid"] = int(l[4])
		d["cli_addr"] = address
		d["UDP_server_sock"] = UDPServerSocket
		d["final_bid"] = "NA"
		d["bidder_id"] = "NA"
		d["port"] = port_available
		#creating a socket for each items
		item_socket_addr = (ip, port_available)
		UDPServeritemSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
		UDPServeritemSocket.bind(item_socket_addr)
		d["UDP_item_sock"] = UDPServeritemSocket
		# with open("item_db", 'a') as f:
		# 	f.write(l[0] + "," + l[1] + "," + str(port_available) + "\n")

		# placing the port for the item in item database
		new_item = Item.query.get(d["id"])
		print(port_available)
		new_item.port = port_available
		db.session.commit()
		port_available += 1
		#clientMsg = "Message from Client:{}".format(message)
		#clientIP  = "Client IP Address:{}".format(address)
		print("Starting bid for new item")
		t = Thread(target=server_item_thread, args = (d,))  #thread to maintian the item bidding
		t.start()
		#place it in thread
		
# if sys.argv[1] == '-s':
# 	server(sys.argv[2], int(sys.argv[3]))
# elif sys.argv[1] == "-cs":
# 	client_seller(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
# elif sys.argv[1] == "-cb":
# 	client_buyer(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
