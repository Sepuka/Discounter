#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from config import Config
from logger import Logger
from db import DB
import sys
from abstractmodule import AbstractModule

class Infoskidka(AbstractModule):
    _conf           = None
    _log            = None
    _db             = None

    def __init__(self):
        self._conf = Config('/srv/www/Discounter/config.cfg')
        self._log = Logger()
        self._db = DB()
        self._log.info('Инициализирован модуль %s', __name__)

    def parse(self):
        self._log.debug('Запущен парсер %s', __name__)
