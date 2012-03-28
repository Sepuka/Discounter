#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from config import Config
from logger import Logger
from db import DB, ENABLED_RESOURCE, DISABLED_RESOURCE
import sys, grab, datetime
from abstractmodule import AbstractModule
from grabber import FailedExtractURLException
from functools import partial
from time import sleep

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
        query = """SELECT id, url FROM resource WHERE module=%s AND enabled=%s"""
        self._db.execute(query, self.__class__.__name__.lower(), ENABLED_RESOURCE)
        if self._db.cursor.rowcount:
            self._startURL = self._db.cursor.fetchall()
        else:
            raise FailedExtractURLException('Ошибка извлечения адреса модуля %s' % __name__)

    def _getCategoriesArea(self):
        """
        Получение области данных содержащих ссылки на категории и их описание
        А также описание категории
        @return lxml.html.HtmlElement
        """
        pattern = '//*/ul[@class="c_catalog"]'
        try:
            return self._grab.xpath(pattern)
        except grab.error.DataNotFound:
            self.critical('Не удалось получить область ссылок на категории')
            raise

    def _getGoodsArea(self):
        """
        Получение области данных содержащих ссылки на товары
        и их короткое описание
        @return lxml.html.HtmlElement
        """
        pattern = '//*/table[@class="shopwindow skidkiTable"]'
        try:
            return self._grab.xpath(pattern)
        except grab.error.DataNotFound:
            self.critical('Не удалось получить область ссылок на товары')
            raise

    def _getCategoryListBlocks(self, linksArea):
        """
        Получение списка блоков содержащих категории
        Возвращает список элементов lxml.html.HtmlElement
        @return list
        """
        pattern = 'li[starts-with(@class, "ct")]'
        try:
            return linksArea.xpath(pattern)
        except grab.error.DataNotFound:
            self.critical('Не удалось получить список блоков содержащих категории')
            raise

    def _getGoodLinks(self, linksArea):
        """
        Получение списка ссылок на магазины предоставляющие скидки
        @return list
        """
        pattern = 'tr/td[starts-with(@class, "actionText")]/a'
        try:
            return map(lambda elem: elem.attrib['href'], linksArea.xpath(pattern))
        except grab.error.DataNotFound:
            self.critical('Не удалось получить список блоков содержащих ссылку на товар')
            raise

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

    def _setCategory(self, id_resource, category, subcategory):
        """
        Добавление категории и подкатегории
        Если категория в ресурсе уже существует, она затрется, при этом
        удалятся все товары из таблицы good
        @return int
        """
        query = """REPLACE INTO category SET id_resource=%s, category=%s, subcategory=%s"""
        return self._db.execute(query, id_resource, category, subcategory)

    def _preparePageURL(self, url):
        """
        Подготовка адреса страницы со ссылками на магазины
        Магазины хранятся постранично
        @return string
        """
        self._currentPage += 1
        return '%s/page.%d.html' % (url[:url.rfind('.')], self._currentPage)

    def _processDiscountList(self, id_resource, id_category, url):
        patternDiscountBlock = '//*/div[@class="actions_list"]'
        patternDiscountItem = '//*/div[@class="action_item"]'
        patternTitle = 'strong'
        patternDescription = 'p[@itemprop="description"]'
        patternStartDate = 'ul/li/time[@itemprop="startDate"]'
        patternEndDate = 'ul/li/time[@itemprop="endDate"]'
        query = """INSERT INTO good SET id_resource=%s, id_category=%s, url=%s, store=%s,""" +\
                """title=%s, description=%s, beginDate=%s, endDate=%s"""
        try:
            store = self._grab.xpath('//*/h2/span[@itemprop="name"]').text
            discountBlock = self._grab.xpath(patternDiscountBlock)
            for item in discountBlock.xpath(patternDiscountItem):
                title = item.find(patternTitle).text
                try:
                    description = item.find(patternDescription).text
                except AttributeError:
                    description = None
                try:
                    start = item.find(patternStartDate).text
                    start = datetime.datetime.strptime(start, '%d.%m.%y').strftime('%Y-%m-%d')
                except AttributeError:
                    start = None
                try:
                    end = item.find(patternEndDate).text
                    end = datetime.datetime.strptime(end, '%d.%m.%y').strftime('%Y-%m-%d')
                except AttributeError:
                    end = None
                #TODO разбор процентов, адресов, метро
                self._db.execute(query, id_resource, id_category, url, store, title, description, start, end)
        except grab.error.DataNotFound:
            self.critical('Ошибка обработки "%s"', url)

    def _parseStore(self, id_resource, id_category, url):
        self.info('Грабим %s', url)
        self._grab.go(url)
        if self._grab.response.code <> 200:
            self.warning('"%s" недоступен. Код ответа "%s"', url, self._grab.status)
            return
        self._processDiscountList(id_resource, id_category, url)

    def parse(self):
        """
        Основной метод
        """
        self.debug('Запущен парсер')
        self._getStartURL()
        for url in self._startURL:
            id_resource = url[0]
            url = url[1]
            self.debug('Обработка узла %s (id %s)', url, id_resource)
            self._grab.go(url)
            self._grab.tree.make_links_absolute(url)
            # Получим область ссылок с описанием категорий и подкатегорий
            linksArea = self._getCategoriesArea()
            # Из области ссылок получаем блоки категорий
            for block in self._getCategoryListBlocks(linksArea):
                categoryName = self._getCategoryName(block)
                self.debug('Обрабатываю категорию "%s"', categoryName)
                subCategoryLinks = self._getSubCategoriesLinks(block)
                self.debug('Найдено %d подкатегорий', len(subCategoryLinks))
                # Из категории получаем подкатегории и в них уже заходим
                for link in subCategoryLinks:
                    self.debug('Обрабатываю подкатегорию %s (%s)', link.text, link.attrib['href'])
                    # Сохраним категорию/подкатегорию в БД
                    id_category = self._setCategory(id_resource, categoryName, link.text)
                    # Постраничный перебор категории
                    while self._grab.response.code == 200:
                        pageURL = self._preparePageURL(link.attrib['href'])
                        self.debug('Переход на страницу %s', pageURL)
                        self._grab.go(pageURL)
                        # Находим область со ссылками на товары
                        goodsArea = self._getGoodsArea()
                        # Получаем список ссылок на магазины и грабим их
                        for store in self._getGoodLinks(goodsArea):
                            self._parseStore(id_resource, id_category, store)
                            sleep(self._conf.getfloat('behavior', 'resourceDelay'))
                        # На странице находится таблица со списком ссылок и коротких описаний на товары
                        sleep(self._conf.getfloat('behavior', 'pageDelay'))
                    self.debug('В подкатегории "%s" обработано %d страниц', link.text, self._currentPage)
                    sleep(self._conf.getfloat('behavior', 'categoryDelay'))
                    return # выход
                return # выход
            sleep(self._conf.getfloat('behavior', 'resourceDelay'))
