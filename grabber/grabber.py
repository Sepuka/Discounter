#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from config import Config
from logger import Logger

class Grabber(object):
    _conf   = None
    _log    = None

    def __init__(self, configPath):
        self._conf = Config(configPath)
        self._log = Logger()
        self._log.info('Запущен discounter')

if __name__ == '__main__':
    grabber = Grabber('/srv/www/Discounter/config.cfg')
