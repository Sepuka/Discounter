#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from config import Config
from logger import Logger
from db import DB, ENABLED_RESOURCE, DISABLED_RESOURCE
import sys
from abstractmodule import AbstractModule
import grab
from grabber import FailedExtractURLException
from functools import partial

class Infoskidka(AbstractModule):
    _conf           = None
    _log            = None
    _db             = None
    _startURL       = None
    _grab           = None
    # Словарь имен вызванных логов для partial
    _logNamesPart   = {}

    def __init__(self):
        self._conf = Config('/srv/www/Discounter/config.cfg')
        self._log = Logger()
        self._db = DB()
        self._grab = grab.Grab()
        self._log.info('Инициализирован модуль %s', self.__class__.__name__)

    def __getattr__(self, name):
        try:
            return self._logNamesPart[name]
        except KeyError:
            obj = getattr(self._log, name)
            if obj is not None:
                part = partial(obj, moduleName=self.__class__.__name__)
                self._logNamesPart[name] = part
                return part

    def _getStartURL(self):
        """
        Получение кротежа адресов узлов с которого следует начать обработку
        Адрес узла должен представлять собой страницу со ссылками на различные
        категории скидок
        @return None
        """
        query = """SELECT url FROM resource WHERE module=%s AND enabled=%s"""
        self._db.execute(query, self.__class__.__name__.lower(), ENABLED_RESOURCE)
        if self._db.cursor.rowcount:
            self._startURL = self._db.cursor.fetchall()
        else:
            raise FailedExtractURLException('Ошибка извлечения адреса модуля %s' % __name__)

    def _getCategoriesLinks(self):
        """
        Получает ссылки на страницы со скидками
        @return list
        """
        links = self._grab.xpath_list('//*/a[contains(@href,"/skidki/")]')
        self.info('Найдено %s ссылок', len(links))
        return links

    def _getLinksArea(self):
        try:
            return self._grab.xpath_list('//*/ul[@class="c_catalog"]')
        except grab.error.DataNotFound:
            self.critical('Не удалось получить область ссылок')
            raise

    def parse(self):
        self.debug('Запущен парсер')
        self._getStartURL()
        for url in self._startURL:
            url = url[0]
            self.debug('Обработка узла %s', url)
            self._grab.go(url)
            self._grab.tree.make_links_absolute(url)
            #Получим область ссылок с описанием категорий и подкатегорий
            linksArea = self._getLinksArea()
            #for link in self._getCategoriesLinks():
            #    self.debug('Обрабатываю %s (%s)', link.attrib['href'], link.text)
