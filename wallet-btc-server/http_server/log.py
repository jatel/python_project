#!/usr/bin/env python3

import logging

logger = logging.getLogger('walletBtcServerLogger')
logger.setLevel(logging.DEBUG)

file_handle = logging.FileHandler('wallet_btc_server.log')
file_handle.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handle.setFormatter(formatter)

logger.addHandler(file_handle)
