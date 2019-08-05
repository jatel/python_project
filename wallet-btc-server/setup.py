#!/usr/bin/env python3

import setuptools
version = '0.0.1'

setuptools.setup(
        name='wallet_http_server',     
        version=version,   
        description='wallet http server of blockabc',   
        author='jatel',  
        author_email='jatel@blockabc.com',  
        url='https://github.com/BlockABC/wallet-btc-server',      
        packages=setuptools.find_packages(include=('http_server*',)),                
)