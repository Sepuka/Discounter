#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from config import Config
from logger import Logger, asciify
from db import DB
from modules.abstractmodule import AbstractModule
from traceback import extract_tb, format_list
import sys

class FailedExtractURLException(Exception):
    pass

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
            self._log.debug('Обрабатываю модуль "%s"', module[0])
            # Импорт модуля
            mod_pack = __import__('modules.' + module[0])
            # например <module 'modules' from '/srv/www/Discounter/grabber/modules/__init__.pyc'>
            modName = getattr(mod_pack, dir(mod_pack)[-1])
            # Определение имени модуля (стоит последним)
            # например ['__builtins__', '__doc__', '__file__', '__name__', '__package__', '__path__', 'abstractmodule', 'infoskidka']
            className = modName.__name__.split('.')[-1].capitalize()
            # Капитализация названия и получение класса
            classObj = getattr(modName, className)
            if issubclass(classObj, AbstractModule):
                parser = classObj()
                try:
                    parser.parse()
                except (Exception,), e:
                    self._log.debug('trace:\n%s', '\n'.join(format_list(extract_tb(sys.exc_info()[2]))))
                    self._log.error('Ошибка работы обработчика %s:%s', classObj, e)
            else:
                self._log.error('Класс %s не является потомком %s !', classObj, AbstractModule)

    def _getGrabModules(self):
        """
        Получение кортежа модулей для работы
        @return tuple
        """
        query = """SELECT `module` FROM `resource` WHERE `enabled`='1'"""
        self._db.execute(query)
        if self._db.cursor.rowcount:
            return self._db.cursor.fetchall()
        else:
            return tuple()

if __name__ == '__main__':
    grabber = Grabber('/srv/www/Discounter/config.cfg')
