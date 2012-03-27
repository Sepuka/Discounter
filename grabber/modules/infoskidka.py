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
    # Текущая обрабатываемая страница
    _currentPage    = 0

    def __init__(self):
        self._conf = Config('/srv/www/Discounter/config.cfg')
        self._log = Logger()
        self._db = DB()
        self._grab = grab.Grab()
        self._log.info('Инициализирован модуль', moduleName=self.__class__.__name__)

    def __getattr__(self, name):
        try:
            return self._logNamesPart[name]
        except KeyError:
            obj = getattr(self._log, name)
            if obj is not None:
                part = partial(obj, moduleName=self.__class__.__name__)
                self._logNamesPart[name] = part
                return part
            else:
                self._log.error('Попытка вызова несуществующего типа лога "%s"',
                    name, moduleName=self.__class__.__name__)

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

    def _getLinksArea(self):
        """
        Получение области данных содержащих ссылки и их описание
        А также описание категории
        @return lxml.html.HtmlElement
        """
        pattern = '//*/ul[@class="c_catalog"]'
        try:
            return self._grab.xpath(pattern)
        except grab.error.DataNotFound:
            self.critical('Не удалось получить область ссылок')
            raise

    def _getCategoryListBlocks(self, linksArea):
        """
        Получение списка блоков содержащих категорию
        Возвращает список элементов lxml.html.HtmlElement
        @return list
        """
        pattern = 'li[starts-with(@class, "ct")]'
        return linksArea.xpath(pattern)

    def _getSubCategoriesLinks(self, category):
        """
        Получение списка ссылок на подкатегории
        @param category
        @type lxml.htmlHtmlElement

        @return list
        """
        pattern = 'div/a[contains(@href,"/skidki/")]'
        return category.xpath(pattern)

    def _getCategoryName(self, blockCategories):
        """
        Получение имени категории
        @return string
        """
        pattern = 'div/h3'
        return blockCategories.xpath(pattern)[0].text

    def _getGoods(self, url):
        self.debug('Получение ссылок на скидки в магазинах с "%s"', url)
        self._grab.go(url)
        return []

    def _setCategory(self, category, subcategory):
        """
        Добавление категории и подкатегории
        """
        query = """REPLACE INTO category SET category=%s, subcategory=%s"""
        self._db.execute(query, category, subcategory)

    def _prepareURL(self, url):
        """
        Подготовка адреса страницы со ссылками на магазины
        Магазины хранятся постранично
        @return string
        """
        self._currentPage += 1
        return '%s/page.%d.html' % (url[:url.rfind('.')], self._currentPage)

    def parse(self):
        """
        Основной метод
        """
        self.debug('Запущен парсер')
        self._getStartURL()
        for url in self._startURL:
            url = url[0]
            self.debug('Обработка узла %s', url)
            self._grab.go(url)
            self._grab.tree.make_links_absolute(url)
            # Получим область ссылок с описанием категорий и подкатегорий
            linksArea = self._getLinksArea()
            # Из области ссылок получаем блоки категорий
            for block in self._getCategoryListBlocks(linksArea):
                categoryName = self._getCategoryName(block)
                self.debug('Обрабатываю категорию "%s"', categoryName)
                subCategoryLinks = self._getSubCategoriesLinks(block)
                self.debug('Найдено %d подкатегорий', len(subCategoryLinks))
                for link in subCategoryLinks:
                    self.debug('Обрабатываю подкатегорию %s (%s)', link.text, link.attrib['href'])
                    # Сохраним категорию/подкатегорию в БД
                    self._setCategory(categoryName, link.text)
                    while self._grab.response.code == 200:
                        goods = self._getGoods(self._prepareURL(link.attrib['href']))
                    self.debug('В подкатегории "%s" обработано %d страниц', link.text, self._currentPage)
                    return # выход
                return # выход
