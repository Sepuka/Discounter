#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from config import Config
from logger import Logger
from db import DB, ENABLED_RESOURCE, DISABLED_RESOURCE
import sys
from abstractmodule import AbstractModule
from grab import Grab

class Infoskidka(AbstractModule):
    _conf           = None
    _log            = None
    _db             = None
    _startURL       = None
    _grab           = None

    def __init__(self):
        self._conf = Config('/srv/www/Discounter/config.cfg')
        self._log = Logger()
        self._db = DB()
        self._log.info('Инициализирован модуль %s', __name__)
        self._grab = Grab()

    def _getStartURL(self):
        """
        Получение адреса узла с которого следует начать обработку
        Адрес узла должен представлять собой страницу со ссылками на различные
        категории скидок
        @return string
        """
        query = """SELECT url FROM resource WHERE module=%s AND enabled=%s"""
        self._db.execute(query, self.__class__.__name__.lower(), ENABLED_RESOURCE)
        if self._db.cursor.rowcount:
            return self._db.cursor.fetchone()[0]
        else:
            return None

    def _getCategoriesLinks(self):
        """
        Получает ссылки на страницы со скидками
        @return list
        """
        self._grab.go(self._startURL)
        links = self._grab.xpath_list('//*/a[starts-with(@href,"/skidki/")]')
        self._log.info('Найдено %s ссылок', len(links))
        return links

    def parse(self):
        self._log.debug('Запущен парсер %s', __name__)
        self._startURL = self._getStartURL()
        if self._startURL is None:
            self._log.error('Не удалось получить адрес страницы с категориями')
            return
        else:
            self._log.debug('Обработка узла %s', self._startURL)
        for link in self._getCategoriesLinks():
            self._log.debug('Обрабатываю %s (%s)', link.attrib['href'], link.text)
