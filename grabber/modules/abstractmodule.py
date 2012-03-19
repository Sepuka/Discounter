#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from abc import ABCMeta, abstractmethod, abstractproperty

class AbstractModule(object):
    """
    Абстрактрый класс-интерфейс для модулей
    """
    __metaclass__   = ABCMeta

    @abstractproperty
    def _conf(self):
        """
        Объект конфигурации
        """
        pass

    @abstractproperty
    def _log(self):
        """
        Объект логов
        """
        pass

    @abstractproperty
    def _db(self):
        """
        Объект БД
        """
        pass

    @abstractmethod
    def parse(self):
        """
        Все модули реализуют метод parse
        Запускающий разбор ресурса
        """
        pass
