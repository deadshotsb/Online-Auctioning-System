from flask import render_template, Blueprint, request, redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename
from threading import Lock
from .models import Item, User
from .main import client_seller, client_buyer
from . import db
# , item_time
import datetime
import os

main = Blueprint('views', __name__)
mutex_m1 = Lock()

# showing home page
@main.route('/')
def index():
    page = request.args.get('page', 1, int)
    per_page = 5  # each page contains 5 items
    category = request.args.get('cat')
    # checking the selected category
    if category == 'All':
        items = Item.query.paginate(page=page, per_page=per_page)
    else:
        items = Item.query.filter_by(category=category).paginate(page=page, per_page=per_page)

    # calculating the ending time of the bidding of an item
    end_time = list()
    for item in items.items:
        dur = list(map(int, item.duration.strftime('%H:%M:%S').split(':')))
        raw_end_time = item.start_time + datetime.timedelta(hours=dur[0], minutes=dur[1], seconds=dur[2])
        end_time.append(raw_end_time.strftime("%b %d, %Y %H:%M:%S"))

    try:
        # if the bidding of an item is over then shows which bidder is the winner or shows no one bidded for the item
        with open('server_msg.txt', 'r') as f:
            all_msgs = f.readlines()
            all_msgs_dict = {}
            for msgs in all_msgs:
                w = msgs.split(',')
                if w[1]:
                    w = list(map(int, msgs.split(',')))
                    all_msgs_dict[w[0]] = (w[1], w[2])
                else:
                    all_msgs_dict[w[0]] = (0, 0)

            msg = []
            for k in all_msgs_dict.keys():
                item = Item.query.get(k)
                msg.append("Bidding completed for "+ item.item_name)

                bidder_id = all_msgs_dict[k][0]
                final_bid = all_msgs_dict[k][1]
                if bidder_id == 0 and final_bid == 0:
                    msg.append("Sorry, No bid placed")
                else:
                    user = User.query.get(bidder_id)
                    msg.append("Received " + str(final_bid) + " from " + user.username)
        
        # reading wallet information of each user
        with open('wallet.log', 'r') as f:
            all_wlts = f.readlines()
            all_wlts_dict = {}
            for wallet in all_wlts:
                w = list(map(int, wallet.split(',')))
                all_wlts_dict[w[0]] = w[1]

        return render_template("index.html", items=items, page=page, per_page=per_page, end=end_time, message=msg, amount=all_wlts_dict[current_user.id])
    except:
        return render_template("index.html", items=items, page=page, per_page=per_page, end=end_time)
    # rems = []
    # for i in range(per_page):
    #     try:
    #         if items.items[i]:
    #             rems.append(item_time[items.items[i].pic_name][1])
    #     except:
    #         break

    # , time=datetime.datetime.now(), rems=rems
    # <td>{{ rems[i]-time }}</td>

# selling page
@main.route('/selling', methods=['GET', 'POST'])
def sell():
    amt = request.args.get('amt')
    if request.method == 'POST':
        category = request.form.get('category')
        item_name = request.form.get('name')
        description = request.form.get('description')
        duration = request.form.get('duration')
        duration = datetime.datetime.strptime(duration, '%H:%M').time()
        start_bid = request.form.get('startb')
        
        pic = request.files['item']
        filename = secure_filename(pic.filename)
        mimetype = pic.mimetype

        item = Item.query.filter_by(pic_name=filename).first()
        if item:
            return render_template("selling.html", error='A file with same name already exists!', amount=amt)

        # item_time[filename] = (duration, datetime.datetime.now())
        pic.save(os.path.join(os.path.dirname(__file__), 'static/images/items', filename))

        item = Item(item_name=item_name, item_pic=pic.read(), pic_name=filename, mimetype=mimetype, category=category, description=description, start_time=datetime.datetime.now(), duration=duration, start_bid=start_bid, user=current_user)
        db.session.add(item)  # adding the new item information in the database
        db.session.commit()

        item = Item.query.filter_by(pic_name=filename).first()
        with open("bid.log", 'r') as f:
            temp_bids = f.readlines()
        with open("bid.log", "a") as f:  # updating the bidding info of the new item
            if len(temp_bids) == 0:
                f.write(str(item.id) + ',0,' + str(start_bid))
            else:
                f.write('\n' + str(item.id) + ',0,' + str(start_bid))
        pid = os.fork()
        if pid == 0:  #child process
            client_seller('127.0.0.1', 6000, item.id, current_user.id)  # runs seller function
            # return None
            pass
        else:
        # os.system('start cmd.exe @cmd /k "python main_server.py -cs 127.0.0.1 6000 '+ str(item.id) + '"')

            return redirect(url_for('views.index'))

    return render_template("selling.html", amount=amt)

# shows details of an item
@main.route('/details/<int:id>', methods=['GET', 'POST'])
def details(id):
    item = Item.query.get(id)
    amt = request.args.get('amt')
    msg = request.args.get('msg')
    err = request.args.get('error')
    # if bid:
    #     curr_bid = bid

    end_time = list()
    dur = list(map(int, item.duration.strftime('%H:%M:%S').split(':')))
    raw_end_time = item.start_time + datetime.timedelta(hours=dur[0], minutes=dur[1], seconds=dur[2])
    end_time.append(raw_end_time.strftime("%b %d, %Y %H:%M:%S"))

    # if msg:
    #     with open('bid.log', 'w') as f:
    #         f.write(msg)

    with open('bid.log', 'r') as f:
        all_bids = f.readlines()
        all_bids_dict = {}
        for bid in all_bids:
            w = list(map(int, bid.split(',')))
            all_bids_dict[w[0]] = (w[1], w[2])

        # reading current bidding information
        if msg:
            all_bids_dict[item.id] = (msg.split(';')[0], msg.split(';')[1])
            all_bids = ''
            for key, value in all_bids_dict.items():
                all_bids += str(key) + ',' + str(value[0]) + ',' + str(value[1]) + '\n'
            all_bids = all_bids[:-1]

            with open('bid.log', 'w') as f:
                f.writelines(all_bids)
        else:
            msg = str(all_bids_dict[item.id][0]) + ';' + str(all_bids_dict[item.id][1])

    # <div class="mb-3">
    #     <p>Time Remaining <span class="ms-3 px-2" style="border: 2px black solid;">{{ dt.datetime.now()-item_time[items.items[i].pic_name][1] }}</span></p>
    # </div>

    return render_template("item_details.html", item=item, amount=amt, end=end_time, curr_bid=msg, error=err)

# adds money to wallet
@main.route('/wallet', methods=['POST'])
def add_money():
    amount = request.form.get('amount')
    try:
        if int(amount) > 0:  # checking if valid amount is entered
            with open('wallet.log', 'r') as f:
                all_wlts = f.readlines()
                all_wlts_dict = {}
                for wallet in all_wlts:
                    w = list(map(int, wallet.split(',')))
                    all_wlts_dict[w[0]] = w[1]

            prev_amt = all_wlts_dict[current_user.id]
            all_wlts_dict[current_user.id] = prev_amt + int(amount)  # adding wallet amount
            all_wlts = ''
            for key, value in all_wlts_dict.items():
                all_wlts += str(key) + ',' + str(value) + '\n'
            all_wlts = all_wlts[:-1]

            with open('wallet.log', 'w') as f:
                f.writelines(all_wlts)
    except:
        pass

    return redirect(url_for('views.index'))

# for deleting an item
@main.route('/delete/<int:id>')
def delete_item(id):
    item = Item.query.get_or_404(id)

    with open('server_msg.txt', 'r') as f:
        all_msgs = f.readlines()
        all_msgs_dict = {}
        for msgs in all_msgs:
            w = msgs.split(',')
            if w[1]:
                w = list(map(int, msgs.split(',')))
                all_msgs_dict[w[0]] = (w[1], w[2])
            else:
                all_msgs_dict[int(w[0])] = (0, 0)

    with open('bid.log', 'r') as f:
        all_bids = f.readlines()
        all_bids_dict = {}
        for bid in all_bids:
            w = list(map(int, bid.split(',')))
            all_bids_dict[w[0]] = (w[1], w[2])

    try:   # if the item is deleted after bidding is completed
        del all_msgs_dict[item.id]

        all_msgs = ''
        for key, value in all_msgs_dict.items():
            bidder_id = value[0]
            final_bid = value[1]
            if bidder_id == 0 and final_bid == 0:
                all_msgs += str(key) + ',,\n'
            else:
                all_msgs += str(key) + ',' + str(value[0]) + ',' + str(value[1]) + '\n'
        all_msgs = all_msgs[:-1]

        with open('server_msg.txt', 'w') as f:
            f.writelines(all_msgs)
    except:  # if the item is deleted before bidding is completed
        with open('wallet.log', 'r') as f:
            all_wlts = f.readlines()
            all_wlts_dict = {}
            for wallet in all_wlts:
                w = list(map(int, wallet.split(',')))
                all_wlts_dict[w[0]] = w[1]

        # previous highest bidder gets all the money back because the item was deleted before time is over
        high_bidder, high_bid = all_bids_dict[id]
        if high_bidder != 0:
            high_bid -= 1
            prev_amt = all_wlts_dict[high_bidder]
            all_wlts_dict[high_bidder] = prev_amt + high_bid
            
            all_wlts = ''
            for key, value in all_wlts_dict.items():
                all_wlts += str(key) + ',' + str(value) + '\n'
            all_wlts = all_wlts[:-1]

            with open('wallet.log', 'w') as f:
                f.writelines(all_wlts)

    # deletes bid info of that item
    del all_bids_dict[item.id]
    all_bids = ''
    for key, value in all_bids_dict.items():
        all_bids += str(key) + ',' + str(value[0]) + ',' + str(value[1]) + '\n'
    all_bids = all_bids[:-1]

    with open('bid.log', 'w') as f:
        f.writelines(all_bids)

    db.session.delete(item)  # deleting item from the database
    db.session.commit()

    return redirect(url_for('views.index'))

# bidding is handled
@main.route('/bid/<int:id>', methods=['POST'])
def item_bid(id):
    bid_value = request.form.get('bid')
    bid_value = bid_value.split('.')[0]
    error = ''
    with open('bid.log', 'r') as f:
        all_bids = f.readlines()
        all_bids_dict = {}
        for bid in all_bids:
            w = list(map(int, bid.split(',')))
            all_bids_dict[w[0]] = (w[1], w[2])
        curr_bid = str(all_bids_dict[id][0]) + ';' + str(all_bids_dict[id][1])

    with open('wallet.log', 'r') as f:
        all_wlts = f.readlines()
        all_wlts_dict = {}
        for wallet in all_wlts:
            w = list(map(int, wallet.split(',')))
            all_wlts_dict[w[0]] = w[1]
    try:
        if all_wlts_dict[current_user.id] < int(bid_value):  # if tries to bid beyond his/her wallet amount
            msg = curr_bid
            error = 'Insufficient balance in your wallet'
        else:
            msg = client_buyer('127.0.0.1', id, current_user.id, int(bid_value))
            if msg.split(';')[0] == "failure":   # if the new bid is not the highest bid
                msg = curr_bid.split(';')[0] + ';' + msg.split(';')[1]
        # bid = int(msg.split(';')[1]) + 1
        # if curr_money.amount < bid:
        #     msg = curr_bid
        #     error = 'Insufficient balance in your wallet'
        # elif msg.split(';')[0] == "failure":
        #     msg = curr_bid.split(';')[0] + ';' + msg.split(';')[1]
        # else:
        #     mutex_m1.acquire()
        #     try:
        #         if curr_bid.split(';')[0] == '0':
        #             curr_money.amount = Wallet.amount - bid
        #         else:
        #             prev_money = Wallet.query.filter_by(user_id=int(curr_bid.split(';')[0])).first()
        #             print(prev_money.user_id, prev_money.amount)
        #             print(curr_money.user_id,curr_money.amount)
        #             prev_money.amount = Wallet.amount + int(curr_bid.split(';')[1]) - 1
        #             curr_money.amount = Wallet.amount - bid
        #         db.session.commit()
        #     finally:
        #         mutex_m1.release()
    except:  # if the bid value is invalid
        msg = curr_bid
        error = 'Please enter integer values starting from the current bidding value'

    with open('wallet.log', 'r') as f:
        all_wlts = f.readlines()
        all_wlts_dict = {}
        for wallet in all_wlts:
            w = list(map(int, wallet.split(',')))
            all_wlts_dict[w[0]] = w[1]

    return redirect(url_for('views.details', id=id, msg=msg, error=error, amt=all_wlts_dict[current_user.id]))