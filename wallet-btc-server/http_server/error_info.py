#!/usr/bin/env python3


# error code
SUCCESS = 0
UNKNOW_ERROR = -1 
SOCKET_ERROR = -2
RANGE_ERROR = -3
PARAM_ERROR = -4
NETWORK_ERROR = -5


# error code and error message
error_message = {
    SUCCESS: "success",
    UNKNOW_ERROR: "unknow error",
    SOCKET_ERROR: "socket error",
    RANGE_ERROR: "out of range",
    PARAM_ERROR: "invalid params",
    NETWORK_ERROR: "network request error"
}