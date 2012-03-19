#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from config import Config
from logger import Logger
from db import DB
from modules import *

#TODO Написать перехватчик ошибок (как он там называется)

class Grabber(object):
    _conf   = None
    _log    = None
    _db     = None

    def __init__(self, configPath):
        self._conf = Config(configPath)
        self._log = Logger()
        self._db = DB()
        self._log.info('Запущен discounter')

        modules = self._getGrabModules()
        self._log.info('Предстоит выполнить %d модулей', len(modules))
        self._runGrabModules(modules)

    def _runGrabModules(self, modules):
        """
        Запуск требуемых модулей
        @param: modules Кортеж модулей
        @type: tuple
        """
        for module in modules:
            self._log.debug('Обрабатываю модуль "%s"', module)

    def _getGrabModules(self):
        """
        Получение кортежа модулей для работы
        @return tuple
        """
        query = """SELECT `module` FROM `resource` WHERE `enabled`='1'"""
        self._db.execute(query)
        if self._db.cursor.rowcount:
            return self._db.cursor.fetchone()
        else:
            return tuple()

if __name__ == '__main__':
    grabber = Grabber('/srv/www/Discounter/config.cfg')
