#!/usr/bin/env python3

from hashlib import sha256
from datetime import datetime
import json
import asyncio
from .log import logger
from . import rpc_call


Base58Alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def get_index_output_address_value(transaction, index):
    one_output = transaction['vout'][index]
    if 'addresses' not in one_output['scriptPubKey']:
        return '', 0
    addresses = one_output['scriptPubKey']['addresses']
    result_address = ''
    if 0 != len(addresses):
        result_address = addresses[0]
    value = one_output['value']
    result_value = int(value * 100000000)
    return result_address, result_value


def is_transaction_coinbase(transaction):
    input = transaction['vin']
    if 'coinbase' in input[0]:
        return True
    else:
        return False


def get_input_list_txid_vout(transaction):
    result = []
    if is_transaction_coinbase(transaction):
        return result
    
    input = transaction['vin']
    for one_input in input:
        result.append({'txid': one_input['txid'], 'vout': one_input['vout']})
    return result


def base58decode(data):
    result = 0
    for d in data:
        charIndex = Base58Alphabet.find(d)
        result = result * len(Base58Alphabet)
        result = result + charIndex
    decoded = hex(result)
    return decoded

def check_address(address):
    for d in address:
        charIndex = Base58Alphabet.find(d)
        if -1 == charIndex:
            return False
    return True

def get_script_hash(address):
    hex_address = base58decode(address)
    pub_key_hash = hex_address[2:len(hex_address) - 8]
    
    if 0 != len(pub_key_hash) % 2:
        pub_key_hash = '0' + pub_key_hash

    script = "76a914" + pub_key_hash + "88ac"
    temp = sha256(bytes.fromhex(script)).digest().hex()
    result = ''
    index = 0
    lenght = len(temp)
    while index < lenght:
        result = temp[index:index+2] + result
        index += 2
    return result


def get_address_list_and_dict_hash_list_by_address(address_batch):
    address_list = []
    address_dict = {}

    for one_address in address_batch:
        one_address_hash = get_script_hash(one_address)
        address_list.append(one_address_hash)
        address_dict[one_address_hash] = one_address
    return address_list, address_dict

def get_transaction_by_txid(txid):
    one_response = rpc_call.get_transaction_by_txid(txid)
    if 'error' in one_response:
        return False, {}
    transaction = one_response['result']

    # input ingo
    input = []
    input_value_sum = 0
    input_txid_vout = get_input_list_txid_vout(transaction)
    for one_txid_vout in input_txid_vout:
        one_txid_response = rpc_call.get_transaction_by_txid(one_txid_vout['txid'])
        if 'error' in one_txid_response:
            continue
        one_address, one_value = get_index_output_address_value(one_txid_response['result'], one_txid_vout['vout'])
        input.append({"from_address": one_address, "from_txid":one_txid_vout['txid'], "vin_index":one_txid_vout['vout'], "value": one_value})
        input_value_sum += one_value
 
    # output info
    output = []
    output_value_sum = 0
    output_length = len(transaction['vout'])
    index = 0
    while index < output_length:
        one_address, one_value = get_index_output_address_value(transaction, index)
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

    return True, {
                    'txid': transaction['txid'],
                    'blockhash': block_hash,
                    'iscoinbase': is_transaction_coinbase(transaction),
                    'fee': input_value_sum - output_value_sum,
                    'inputs': input,
                    'outputs': output,
                    'confirmations': confirmations,
                    'blocktime': utc_time
                }

def get_transaction_by_txid_batch(txid_batch):
    response = rpc_call.get_transaction_by_txid_batch(txid_batch)
    result_transaction_dict = {}
    for one_response in response:
        if 'error' in one_response:
            logger.error("get_transaction_by_txid_batch get_transaction_by_txid_batch one error: " + json.dumps(one_response, ensure_ascii=False))
            continue
        result_transaction_dict[one_response['id']] = one_response['result']

    result_transaction = []
    index = 0
    txid_lenght = len(txid_batch)
    while index < txid_lenght:
        if index in result_transaction_dict:
            result_transaction.append(result_transaction_dict[index])
        index = index + 1

    input_txid = []
    for one_result_transaction in result_transaction:
        input_txid_vout = get_input_list_txid_vout(one_result_transaction)
        for one_txid_vout in input_txid_vout:
            input_txid.append(one_txid_vout['txid'])
    real_input_txid = list(set(input_txid))
    

    input_transaction_dict = {}
    real_input_txid_length = len(real_input_txid)
    page_length = 20
    page_num = real_input_txid_length // page_length
    page_other = real_input_txid_length % page_length
    page_index = 0
    while page_index < page_num:
        input_response = rpc_call.get_transaction_by_txid_batch(real_input_txid[page_length*page_index:page_length*(page_index+1)])
        for one_input_response in input_response:
            if 'error' in one_input_response:
                logger.error("get_transaction_by_txid_batch get_transaction_by_txid_batch one error: " + json.dumps(one_input_response, ensure_ascii=False))
                continue
            input_transaction_dict[one_input_response['result']['txid']] = one_input_response['result']
        page_index = page_index + 1

    if page_other != 0:
        input_response = rpc_call.get_transaction_by_txid_batch(real_input_txid[page_length*page_index:])
        for one_input_response in input_response:
            if 'error' in one_input_response:
                logger.error("get_transaction_by_txid_batch get_transaction_by_txid_batch one error: " + json.dumps(one_input_response, ensure_ascii=False))
                continue
            input_transaction_dict[one_input_response['result']['txid']] = one_input_response['result']

    result = []
    for one_result_transaction in result_transaction:
        # input info
        input = []
        input_value_sum = 0
        input_txid_vout = get_input_list_txid_vout(one_result_transaction)
        for one_txid_vout in input_txid_vout:
            if one_txid_vout['txid'] in input_transaction_dict:
                one_address, one_value = get_index_output_address_value(input_transaction_dict[one_txid_vout['txid']], one_txid_vout['vout'])
                input.append({"from_address": one_address, "from_txid":one_txid_vout['txid'], "vin_index":one_txid_vout['vout'], "value": one_value})
                input_value_sum += one_value
            else:
                input.append({"from_address": "", "from_txid":one_txid_vout['txid'], "vin_index":one_txid_vout['vout'], "value": 0})
                input_value_sum += 0
       
        # output info
        output = []
        output_value_sum = 0
        output_length = len(one_result_transaction['vout'])
        index = 0
        while index < output_length:
            one_address, one_value = get_index_output_address_value(one_result_transaction, index)
            output.append({'to_address': one_address, 'vout_index': index, 'value': one_value, 'type': one_result_transaction['vout'][index]['scriptPubKey']['type'], 'asm': one_result_transaction['vout'][index]['scriptPubKey']['asm']})
            output_value_sum += one_value
            index += 1

        utc_time = ""
        if 'blocktime' in one_result_transaction:
            utc_time = datetime.utcfromtimestamp(one_result_transaction['blocktime']).isoformat() + '+0000'
    
        block_hash = ''
        if 'blockhash' in one_result_transaction:
            block_hash = one_result_transaction['blockhash']

        confirmations = -1
        if 'confirmations' in one_result_transaction:
            confirmations = one_result_transaction['confirmations']

        result.append({
                    'txid': one_result_transaction['txid'],
                    'blockhash': block_hash,
                    'iscoinbase': is_transaction_coinbase(one_result_transaction),
                    'fee': input_value_sum - output_value_sum,
                    'inputs': input,
                    'outputs': output,
                    'confirmations': confirmations,
                    'blocktime': utc_time
                })
    return result

def get_transaction_without_input_address_by_txid_batch_async(txid_batch):
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    loop = asyncio.get_event_loop()
    tasks = []
    for txid in txid_batch:
        tasks.append(asyncio.ensure_future(rpc_call.get_transaction_by_txid_from_node_async(txid)))
    loop.run_until_complete(asyncio.wait(tasks))

    result = []
    for task in tasks:
        result.append(task.result())

    return result

# slow
def get_transaction_by_txid_batch_async(txid_batch):
    # get transaction info
    result_transaction = get_transaction_without_input_address_by_txid_batch_async(txid_batch)
 
    # get input txid
    input_txid = []
    for one_result_transaction in result_transaction:
        input_txid_vout = get_input_list_txid_vout(one_result_transaction)
        for one_txid_vout in input_txid_vout:
            input_txid.append(one_txid_vout['txid'])
    real_input_txid = list(set(input_txid))

    input_transaction_dict = {}
    all_input_transaction = get_transaction_without_input_address_by_txid_batch_async(real_input_txid)
    for one_input_transaction in all_input_transaction:
        input_transaction_dict[one_input_transaction['txid']] = one_input_transaction

    result = []
    for one_result_transaction in result_transaction:
        # input info
        input = []
        input_value_sum = 0
        input_txid_vout = get_input_list_txid_vout(one_result_transaction)
        for one_txid_vout in input_txid_vout:
            if one_txid_vout['txid'] in input_transaction_dict:
                one_address, one_value = get_index_output_address_value(input_transaction_dict[one_txid_vout['txid']], one_txid_vout['vout'])
                input.append({"from_address": one_address, "from_txid":one_txid_vout['txid'], "vin_index":one_txid_vout['vout'], "value": one_value})
                input_value_sum += one_value
            else:
                input.append({"from_address": "", "from_txid":one_txid_vout['txid'], "vin_index":one_txid_vout['vout'], "value": 0})
                input_value_sum += 0
       
        # output info
        output = []
        output_value_sum = 0
        output_length = len(one_result_transaction['vout'])
        index = 0
        while index < output_length:
            one_address, one_value = get_index_output_address_value(one_result_transaction, index)
            output.append({'to_address': one_address, 'vout_index': index, 'value': one_value, 'type': one_result_transaction['vout'][index]['scriptPubKey']['type'], 'asm': one_result_transaction['vout'][index]['scriptPubKey']['asm']})
            output_value_sum += one_value
            index += 1

        utc_time = ""
        if 'blocktime' in one_result_transaction:
            utc_time = datetime.utcfromtimestamp(one_result_transaction['blocktime']).isoformat() + '+0000'
    
        block_hash = ''
        if 'blockhash' in one_result_transaction:
            block_hash = one_result_transaction['blockhash']

        confirmations = -1
        if 'confirmations' in one_result_transaction:
            confirmations = one_result_transaction['confirmations']

        result.append({
                    'txid': one_result_transaction['txid'],
                    'blockhash': block_hash,
                    'iscoinbase': is_transaction_coinbase(one_result_transaction),
                    'fee': input_value_sum - output_value_sum,
                    'inputs': input,
                    'outputs': output,
                    'confirmations': confirmations,
                    'blocktime': utc_time
                })
    return result

# async 
async def get_transaction_by_txid_async(txid):
    transaction = rpc_call.get_transaction_by_txid_from_node(txid)
    if not transaction:
        return {}
    
    # input info
    input = []
    input_value_sum = 0
    input_txid_vout = get_input_list_txid_vout(transaction)
    all_txid_vout_txid = []
    for one_txid_vout in input_txid_vout:
        all_txid_vout_txid.append(one_txid_vout['txid'])

    all_txid_vout_transaction = get_transaction_without_input_address_by_txid_batch_async(all_txid_vout_txid)

    for one_txid_vout in input_txid_vout:
        one_txid_transaction = {}
        bool_find = False
        for one_transaction in all_txid_vout_transaction:
            if one_transaction['txid'] == one_txid_vout['txid']:
                one_txid_transaction = one_transaction
                bool_find = True
                break

        if not bool_find:
            continue

        one_address, one_value = get_index_output_address_value(one_txid_transaction, one_txid_vout['vout'])
        input.append({"from_address": one_address, "from_txid": one_txid_vout['txid'], "vin_index": one_txid_vout['vout'], "value": one_value})
        input_value_sum += one_value
 
    # output info
    output = []
    output_value_sum = 0
    output_length = len(transaction['vout'])
    index = 0
    while index < output_length:
        one_address, one_value = get_index_output_address_value(transaction, index)
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

    return {
                    'txid': transaction['txid'],
                    'blockhash': block_hash,
                    'iscoinbase': is_transaction_coinbase(transaction),
                    'fee': input_value_sum - output_value_sum,
                    'inputs': input,
                    'outputs': output,
                    'confirmations': confirmations,
                    'blocktime': utc_time
                }


