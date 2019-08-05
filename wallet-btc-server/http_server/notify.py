#!/usr/bin/env python3

import gevent
from gevent import monkey
monkey.patch_all()
import requests
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import json
from . import config
from . import utility
from .log import logger

all_unconfirmed_transaction = []

def get_notify_address():
    '''get address from notify hub'''

    try:
        # requset 
        url = config.config['notify_server_address'] + "/v1/cids"
        payload={"chain_type":"BTC", "chain_id":"mainnet"}
        response = requests.get(url, params=payload)
        if 200 != response.status_code:
            logger.error("get_notify_address response status is not 200, code: " + str(response.status_code))
            return False, []

        # result info
        result = response.json()
        if 0 != result['errno']:
            logger.error("get_notify_address error, error number: " + str(result['errno']) + " , error message: " + result['errmsg'])
            return False, []
    except:
        logger.error("get_notify_address has an exception")
        return False, []


    return True, result["data"]["addresses"]


def get_unconfirmed_transaction_and_notify():
    ''' get different unconfirmed transaction and push info to notify hub'''

    try:
        # get all unconfirmed transaction
        payload = {"jsonrpc": "2.0", "method": "getrawmempool", "params": {}, "id": 1}
        url = 'http://' + config.config['rpcaddress'] + ':' + str(config.config['rpcport'])
        response = requests.post(url, data=json.dumps(payload), auth=(config.config['rpcuser'], config.config['rpcpassword']))
        if 200 != response.status_code:
            logger.error("get_unconfirmed_transaction_and_notify getrawmempool response status is not 200, code: " + str(response.status_code))
            return

        one_response = response.json()
        if one_response['error'] is not None:
            logger.error("get_unconfirmed_transaction_and_notify getrawmempool error, error number: " + str(one_response['error']['code']) + " , error message: " + one_response['error']['message'])
            return

    except:
        logger.error("get_unconfirmed_transaction_and_notify has an exception")
        return

    new_unconfirmed_transaction = one_response['result']
    global all_unconfirmed_transaction
    diff_unconfirmed_transaction = list(set(new_unconfirmed_transaction).difference(set(all_unconfirmed_transaction)))

     # get notify address
    isOk, notify_address = get_notify_address()
    if not isOk:
        return 
    
    # set new transactions
    all_unconfirmed_transaction = new_unconfirmed_transaction
    if 0 == len(diff_unconfirmed_transaction):
        return

    if 0 == len(notify_address):
        return

    # new task
    gevent.spawn(notify_new_unconfirmed_transaction, diff_unconfirmed_transaction, notify_address)


def notify_new_unconfirmed_transaction(diff_unconfirmed_transaction, notify_address):
    # get transaction info
    unconfirmed_transaction_info = []
    for one_diff_txid in diff_unconfirmed_transaction:
        isTrue, one_deff_transaction_info = utility.get_transaction_by_txid(one_diff_txid)
        if isTrue:
            unconfirmed_transaction_info.append(one_deff_transaction_info)

    # notify
    push_list = []
    for one_transaction in unconfirmed_transaction_info:
        # inputs
        for one_input in one_transaction['inputs']:
            for one_address in notify_address:
                if one_address['name'] == one_input['from_address']:
                    push_list.append({'chain_type':one_address['chain_type'],
                    'chain_id': one_address['chain_id'],
                    'msg_type':2,
                    'cid': one_address['cid'],
                    'msg_id': str(2)+one_input['from_txid']+str(one_input['vin_index']),
                    'language': one_address['language'],
                    'token_name': 'BTC',
                    'name': one_address['name'],
                    'platform': one_address['platform']})

        # outputs
        for one_output in one_transaction['outputs']:
            for one_address in notify_address:
                if one_address['name'] == one_output['to_address']:
                    push_list.append({'chain_type':one_address['chain_type'],
                    'chain_id': one_address['chain_id'],
                    'msg_type':1,
                    'cid': one_address['cid'],
                    'msg_id': str(1)+one_transaction['txid']+str(one_output['vout_index']),
                    'language': one_address['language'],
                    'token_name': 'BTC',
                    'name': one_address['name'],
                    'platform': one_address['platform']})

    # send notify
    if 0 == len(push_list):
        return

    url = config.config['notify_server_address'] + "/v1/push"
    payload = {'push_list': push_list}
    response = requests.post(url, data=json.dumps(payload))
    if 200 != response.status_code:
        logger.error("notify info: " + json.dumps(push_list))
        logger.error("notify_new_unconfirmed_transaction push info response status is not 200, code: " + str(response.status_code))

    # result info
    result = response.json()
    if 0 != result['errno']:
        logger.error("notify info: " + json.dumps(push_list))
        logger.error("notify_new_unconfirmed_transaction push info error, error number: " + str(result['errno']) + " , error message: " + result['errmsg'])
    logger.info("notify info: " + json.dumps(push_list))
    logger.info("get_unconfirmed_transaction_and_notify success!!!")


def timer_task():
    ''' all time task '''

    scheduler = BlockingScheduler()
    scheduler.add_job(get_unconfirmed_transaction_and_notify, 'interval', seconds=config.config['unconfirmed_transaction_interval'])
    scheduler.start()
