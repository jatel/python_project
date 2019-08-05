#!/usr/bin/env python3

import yaml
import os

config = {}

def read_config():
    cur_path = os.path.dirname(os.path.realpath(__file__))
    yaml_file = open(os.path.join(cur_path, "config.yaml"), 'r', encoding='utf-8')
    info = yaml_file.read()
    global config
    config = yaml.load(info, Loader=yaml.FullLoader)


read_config()