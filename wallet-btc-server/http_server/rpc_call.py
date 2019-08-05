#!/usr/bin/env python3

from . import electrumx_tcp
from . import config
from .log import logger
import json
import requests

def get_transaction_by_txid(txid):
    one_request = {"jsonrpc": "2.0", "method": "blockchain.transaction.get", "params": {'tx_hash':txid, 'verbose': True}, "id": 1}
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)

def get_transaction_by_txid_batch(txid_batch):
    one_request = []
    index = 0
    for txid in txid_batch:
        one_request.append({"jsonrpc": "2.0", "method": "blockchain.transaction.get", "params": {'tx_hash':txid, 'verbose': True}, "id": index})
        index += 1
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)

def get_address_unspent(address):
    one_request = {"jsonrpc": "2.0", "method": "blockchain.scripthash.listunspent", "params": {'scripthash': address}, "id": 2}
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)

def get_address_unspent_batch(address_batch):
    one_request = []
    index = 0
    for one_address in address_batch:
        one_request.append({"jsonrpc": "2.0", "method": "blockchain.scripthash.listunspent", "params": {'scripthash': one_address}, "id": index})
        index += 1
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)

def get_fee_with_number(number):
    one_request = {"jsonrpc": "2.0", "method": "blockchain.estimatefee", "params": {'number': number}, "id": 2}
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)

def get_address_balance(address):
    one_request = {"jsonrpc": "2.0", "method": "blockchain.scripthash.get_balance", "params": {'scripthash': address}, "id": 2}
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)

def get_address_balance_batch(address_batch):
    one_request = []
    index = 0
    for one_address in address_batch:
        one_request.append({"jsonrpc": "2.0", "method": "blockchain.scripthash.get_balance", "params": {'scripthash': one_address}, "id": index})
        index += 1
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)

def get_address_history(address):
    one_request = {"jsonrpc": "2.0", "method": "blockchain.scripthash.get_history", "params": {'scripthash': address}, "id": 2}
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)

def get_address_history_batch(address_batch):
    one_request = []
    index = 0
    for one_address in address_batch:
        one_request.append({"jsonrpc": "2.0", "method": "blockchain.scripthash.get_history", "params": {'scripthash': one_address}, "id": index})
        index += 1
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)

def get_address_used_batch(address_batch):
    one_request = []
    index = 0
    for one_address in address_batch:
        one_request.append({"jsonrpc": "2.0", "method": "blockchain.scripthash.has_used", "params": {'scripthash': one_address}, "id": index})
        index += 1
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)

def broadcast_transaction(hex_transaction):
    one_request = {"jsonrpc": "2.0", "method": "blockchain.transaction.broadcast", "params": {'raw_tx': hex_transaction}, "id": 2}
    result = electrumx_tcp.tcp_call(json.dumps(one_request, ensure_ascii=False))
    return  json.loads(result)


def get_transaction_by_txid_from_node(txid):
    payload = {"jsonrpc": "2.0", "method": "getrawtransaction", "params": [txid, True], "id": 1}
    url = 'http://' + config.config['rpcaddress'] + ':' + str(config.config['rpcport'])
    response = requests.post(url, data=json.dumps(payload), auth=(config.config['rpcuser'], config.config['rpcpassword']))
    if 200 != response.status_code:
        logger.error("get_transaction_by_txid_from_node response status is not 200, code: " + str(response.status_code))
        return {}

    one_response = response.json()
    if one_response['error'] is not None:
        logger.error("get_transaction_by_txid_from_node error, error number: " + str(one_response['error']['code']) + " , error message: " + one_response['error']['message'])
        return {}
    return one_response['result']

async def get_transaction_by_txid_from_node_async(txid):
    return get_transaction_by_txid_from_node(txid)
