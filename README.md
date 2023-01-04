# Online-Auctioning-System

This project has been done as a course Term Project of CS69201 of IIT Kharagpur

We have used Flask to make our project

You can install anaconda or through pip, you can create a virtual environment by this command "python3 -m venv <virtualenv>".

Then to activate the virtualenv you have to write
- source <virtualenv_path/activate> (for Linux)
- <virtualenv_path/activate.bat> (for Windows)

Then to install all the required packages, run
- pip install -r requirements.txt

To start the app, run
- python app.py
or
- python3 app.py



An Online Auctioning System is a platform which is similar to an online
shopping environment, with the exception that users have the flexibility of
placing their own evaluation of the product and back off if they feel the
product is over-priced.

We have implemented an User Datagram Protocol (UDP) Server-Client
model to simulate the working of an online auctioning system. Our choice
of UDP over Transaction Control Protocol (TCP) is solely based on the fact
that in real-world scenario, there is a huge traffic involved in bidding for a
profuct and a huge number of users may bid for an item. As UDP is faster
than TCP, hence UDP gets a preference in this regard.

We have divided the clients on seller and buyer client based on choices
given by an user. If an user wishes to sell his product in the website then he
can place his item with an item description. An item description includes
item name, a description, an image, category of the item, starting bid of
the item and duration for which he wishes to place the item on bidding.
A buyer client is a client that wishes to place a bid for an item. We have
implemented a wallet that restricts the bidding of the user in a way that for
a bid to be valid the user needs to have the wallet amount that justifies his
bid amount. Finally, after a bid is completed (timer for the bid expires) we
display the winning bid user name and bid amount(if any) and transfers the
entire amount to the seller of the item.
