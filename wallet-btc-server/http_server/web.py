#!/usr/bin/env python3

from flask import Flask, jsonify, request

# Import the fixer
from werkzeug.contrib.fixers import ProxyFix

from datetime import datetime
from flask_cors import CORS

import requests
import time
import json
from operator import itemgetter

from .log import logger
from . import rpc_call
from . import utility
from . import error_info
from . import config


app = Flask(__name__)

# Use the fixer
app.wsgi_app = ProxyFix(app.wsgi_app)

# cors handle
CORS(app, supports_credentials=True)

@app.route('/btc_price')
def get_btc_price():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&&vs_currencies=usd'
    response = requests.get(url)
    if 200 != response.status_code:
        logger.error("get_btc_price response status is not 200, code: " + str(response.status_code))
        return jsonify(errno=error_info.NETWORK_ERROR,
                   errmsg=error_info.error_message[error_info.NETWORK_ERROR],
                   price=0)
    result = response.json()
    return jsonify(errno=error_info.SUCCESS,
                errmsg=error_info.error_message[error_info.SUCCESS],
                data={'price': result['bitcoin']['usd']})

 
@app.route('/transaction/<txid>')
def get_transaction(txid):
    logger.info("get_transaction txid:" + txid)
    one_response = rpc_call.get_transaction_by_txid(txid)
    if 'error' in one_response:
        return jsonify(errno=one_response['error']['code'],
                   errmsg=one_response['error']['message'],
                   data={})
    transaction = one_response['result']

    # input info
    input = []
    input_value_sum = 0
    input_txid_vout = utility.get_input_list_txid_vout(transaction)
    for one_txid_vout in input_txid_vout:
        one_txid_response = rpc_call.get_transaction_by_txid(one_txid_vout['txid'])
        if 'error' in one_txid_response:
            logger.error("get_transaction_by_txid response has error, " + json.dumps(one_txid_response))
            continue
        one_address, one_value = utility.get_index_output_address_value(one_txid_response['result'], one_txid_vout['vout'])
        input.append({"from_address": one_address, "from_txid":one_txid_vout['txid'], "vin_index":one_txid_vout['vout'], "value": one_value})
        input_value_sum += one_value
 
    # output info
    output = []
    output_value_sum = 0
    output_length = len(transaction['vout'])
    index = 0
    while index < output_length:
        one_address, one_value = utility.get_index_output_address_value(transaction, index)
        output.append({'to_address': one_address, 'vout_index': index, 'value': one_value, 'type': transaction['vout'][index]['scriptPubKey']['type'], 'asm': transaction['vout'][index]['scriptPubKey']['asm']})
        output_value_sum += one_value
        index += 1

    utc_time = ""
    if 'blocktime' in transaction:
        utc_time = datetime.utcfromtimestamp(transaction['blocktime']).isoformat() + '+0000'
    
    block_hash = ''
    if 'blockhash' in transaction:
        block_hash = transaction['blockhash']

    confirmations = -1
    if 'confirmations' in transaction:
        confirmations = transaction['confirmations'] 

    return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data={
                       'txid': transaction['txid'],
                       'blockhash': block_hash,
                       'iscoinbase': utility.is_transaction_coinbase(transaction),
                       'fee': input_value_sum - output_value_sum,
                       'inputs': input,
                       'outputs': output,
                       'confirmations': confirmations,
                       'blocktime': utc_time
                   })


@app.route('/address/unspents', methods=['GET', 'POST'])
def get_unspents():
    # check address
    address_temp = json.loads(request.get_data())
    address = []
    for one_temp_address in address_temp:
        if utility.check_address(one_temp_address):
            address.append(one_temp_address)
    if 0 == len(address):
        return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data={})

    # get unspents
    address_list, address_dict= utility.get_address_list_and_dict_hash_list_by_address(address)
    info_temp = [None]*len(address_list)
    response = rpc_call.get_address_unspent_batch(address_list)
    for one_response in response:
        if 'error' in one_response:
            logger.error("get_address_unspent_batch one response has error, " + json.dumps(one_response))
            continue
        for one_unspent in one_response['result']:
            info_temp[one_response['id']] = {'address': address_dict[address_list[one_response['id']]], 'txid': one_unspent['tx_hash'], 'vout_index': one_unspent['tx_pos'], 'value': one_unspent['value']}
    
    # get real unspent
    info = []
    for one_info in info_temp:
        if one_info is not None:
            info.append(one_info)
    
    return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data=info
    )

@app.route('/recommended_fee_rates')
def get_fee_rate():
    one_response = rpc_call.get_fee_with_number(config.config['blocknum'])
    if 'error' in one_response:
        logger.error("get_fee_with_number response has error, " + json.dumps(one_response))
        return jsonify(errno=one_response['error']['code'],
                   errmsg=one_response['error']['message'],
                   data=[])
    rate = int(one_response['result'] * 100000000)
    index = 4
    info = []
    while index > 0:
        if 4 == index:
            info.append({'weight': index, 'value': rate*config.config['quick']})
        if 3 == index:
            info.append({'weight': index, 'value': rate*config.config['priority']})
        if 2 == index:
            info.append({'weight': index, 'value': rate*config.config['normal']})
        if 1 == index:
            info.append({'weight': index, 'value': rate})
        index = index - 1

    return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data=info
    )


@app.route('/address/balance', methods=['GET', 'POST'])
def get_balance():
    # check address
    address_temp = json.loads(request.get_data())
    address = []
    for one_temp_address in address_temp:
        if utility.check_address(one_temp_address):
            address.append(one_temp_address)
    if 0 == len(address):
        return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data={})

    # get balance
    address_list, address_dict= utility.get_address_list_and_dict_hash_list_by_address(address)
    response = rpc_call.get_address_balance_batch(address_list)
    info = [None]*len(address_list)

    for one_response in response:
        if 'error' in one_response:
            logger.error("get_address_balance_batch one response has error, " + json.dumps(one_response))
            continue
        one_balance = one_response['result']
        info[one_response['id']] = {'address': address_dict[address_list[one_response['id']]], 'balance': float(one_balance['confirmed']) + float(one_balance['unconfirmed'])} 

    return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data=info
    )

@app.route('/address/transactions', methods=['GET', 'POST'])
def get_address_transactions():
    one_request = json.loads(request.get_data())
    if one_request['size'] < 0 or one_request['page'] <= 0:
        return jsonify(errno=error_info.PARAM_ERROR,
                   errmsg=error_info.error_message[error_info.PARAM_ERROR],
                   data={}
        )
    
    # check address
    address_temp = one_request['addresses']
    address = []
    for one_temp_address in address_temp:
        if utility.check_address(one_temp_address):
            address.append(one_temp_address)
    if 0 == len(address):
        return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data={})

    # get all transactions
    all_transactions = []
    address_list, address_dict= utility.get_address_list_and_dict_hash_list_by_address(address)
    response = rpc_call.get_address_history_batch(address_list)
    for one_response in response:
        if 'error' in one_response:
            continue
        all_transactions = all_transactions + one_response['result']

    if 0 == len(all_transactions):
        return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data={}
        )

    # sort transaction
    all_transactions.sort(key=itemgetter('height'), reverse=True)

    index = len(all_transactions) - 1
    while index >= 0 and all_transactions[index]['height'] == 0:
        index = index - 1

    if index >= 0:
        all_transactions = all_transactions[index+1:] + all_transactions[0:index+1]

    if one_request['size'] * (one_request['page'] -1) >= len(all_transactions):
        return jsonify(errno=error_info.RANGE_ERROR,
                   errmsg=error_info.error_message[error_info.RANGE_ERROR],
                   data={}
        )
   
    real_transaction = []
    if one_request['size'] * one_request['page'] > len(all_transactions):
        real_transaction = all_transactions[one_request['size'] * (one_request['page'] - 1):]
    else:
        real_transaction = all_transactions[one_request['size'] * (one_request['page'] - 1):one_request['size'] * one_request['page'] - 1]
    
    real_txid = []
    for one_transaction in real_transaction:
        real_txid.append(one_transaction['tx_hash'])

    info_temp = utility.get_transaction_by_txid_batch(real_txid)

    # sort result
    info = []
    for one_txid in real_txid:
        for one_info in info_temp:
            if one_txid == one_info['txid']:
                info.append(one_info)

    return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data={
                       "pagination": {"page": one_request['page'], 'size': one_request['size']},
                       "list":info
                   }
    )


@app.route('/send_raw_transaction', methods=['GET', 'POST'])
def send_raw_transaction():
    one_request = json.loads(request.get_data())
    one_response = rpc_call.broadcast_transaction(one_request['tx'])
    if 'error' in one_response:
        return jsonify(errno=one_response['error']['code'],
                   errmsg=one_response['error']['message'],
                   data=[])
    return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data={'txid': one_response['result']}
    )


@app.route('/address', methods=['GET', 'POST'])
def get_address_used():
    # check address
    address_temp = json.loads(request.get_data())
    address = []
    for one_temp_address in address_temp:
        if utility.check_address(one_temp_address):
            address.append(one_temp_address)
    if 0 == len(address):
        return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data={})

    # get address used           
    address_list, address_dict= utility.get_address_list_and_dict_hash_list_by_address(address)
    response = rpc_call.get_address_used_batch(address_list)
    info = [None]*len(address_list)

    for one_response in response:
        if 'error' in one_response:
            logger.error("get_address_used_batch one response has error, " + json.dumps(one_response))
            info.append({'address': address_dict[address_list[one_response['id']]], 'used': False})
            continue
        info[one_response['id']] = {'address': address_dict[address_list[one_response['id']]], 'used': one_response['result']}

    return jsonify(errno=error_info.SUCCESS,
                   errmsg=error_info.error_message[error_info.SUCCESS],
                   data=info
    )


def http_task():
    global app
    app.run(host = '0.0.0.0', port=config.config['listen_port'], debug = True)

if __name__ == '__main__':
    http_task()
