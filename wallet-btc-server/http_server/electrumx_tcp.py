#!/usr/bin/env python3
import socket
import time
from . import error_info
from . import config

def tcp_call(request_json):
    try:
        send_info = request_json + "\n"
        electrumx_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	
        electrumx_socket.connect((config.config['host_electrumx'], config.config['port_electrumx']))
        electrumx_socket.sendall(send_info.encode())
    except socket.error:
        return {'error': {'code': error_info.SOCKET_ERROR, 'message': error_info.error_message[error_info.SOCKET_ERROR]}}
    recv_data = ''
    page_data = ''
    while True:
        try:
            page_data = electrumx_socket.recv(1024).decode()
            recv_data += page_data
            if page_data.find("\n")!=-1:
                break
        except:
            return {'error': {'code': error_info.SOCKET_ERROR, 'message': error_info.error_message[error_info.SOCKET_ERROR]}}
    electrumx_socket.close()
    all_recv = recv_data.split("\n", 1)
    return all_recv[0]


# class json rpc request object
class jsonRpcRequest:
    def __init__(self):
        self.jsonrpc = "2.0"
        self.method = ""
        self.params = {}
        self.id = 1


# class json rpc error object
class jsonRpcErrpr:
    def __init__(self,error_code=-32600, error_message="Invalid Request", error_data={}):
        self.code = error_code
        self.message = error_message
        self.data = error_data


# class json rpc response object
class jsonRpcResponse:
    def __init__(self):
        self.jsonrpc = "2.0"
        self.result = {}
        self.error = jsonRpcErrpr()
        self.id = 1