#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

import logging, os
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG
from logging.handlers import TimedRotatingFileHandler
from config import Config

def process_sequence(func):
    u"""
    Декоратор обеспечивающий обработку всех элементов последовательности
    """
    def sequence(arg):
        if isinstance(arg, tuple) or isinstance(arg, list):
            return type(arg)(map(func, arg))
        elif isinstance(arg, dict):
            for key, value in arg.iteritems():
                arg[key] = func(value)
            return arg
        else:
            return func(arg)
    return sequence

@process_sequence
def asciify(data):
    u"""
    Приведение данных к ascii кодеку
    """
    if isinstance(data, unicode):
        return data.encode('utf-8')
    return data

@process_sequence
def utf8fy(data):
    u"""
    Приведение данных в unicode
    """
    if not isinstance(data, unicode):
        try:
            return unicode(data, 'utf-8')
        except (TypeError):
            return unicode(data)
    return data

class Singleton(type):
    def __init__(cls, *args, **kw):
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance

class Logger(object):
    __metaclass__   = Singleton
    __log           = None
    _conf           = None

    def __init__(self):
        self._conf = Config()
        log_path = os.path.join(os.getcwd(), self._conf.get('log', 'path'))
        log_grab = os.path.join(os.getcwd(), self._conf.get('log', 'grab'))
        log_when = 'midnight'

        handler = logging.handlers.TimedRotatingFileHandler(log_path, when=log_when)
        handler_grab = logging.handlers.TimedRotatingFileHandler(log_grab, when=log_when)
        handler.setFormatter(logging.Formatter('%(asctime)-15s %(levelname)-8s %(message)s'))
        handler.setLevel(self._conf.getint('log', 'level'))
        handler_grab.setLevel(self._conf.getint('log', 'grabLevel'))

        self.__log = logging.getLogger('discounter')
        self.__log.setLevel(self._conf.getint('log', 'level'))
        self.__log.addHandler(handler)

        grabLogger = logging.getLogger('grab')
        grabLogger.setLevel(self._conf.getint('log', 'grabLevel'))
        grabLogger.addHandler(handler_grab)

    def _log(self, msg, *args, **kw):
        """
        Запись в лог
        """
        try:
            kw['exc_info']
        except KeyError:
            exc_info = False
        else:
            exc_info = sys.exc_info()
        msg = msg % asciify(args)
        self.__log.log(kw['level'], asciify(msg), exc_info=exc_info)

    def debug(self, msg, *args, **kwargs):
        """
        Запись в лог типа DEBUG
        """
        kwargs['level'] = DEBUG
        self._log(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Запись в лог типа INFO
        """
        kwargs['level'] = INFO
        self._log(msg, *args, **kwargs)
    def warning(self, msg, *args, **kwargs):
        """
        Запись в лог типа WARNING
        """
        kwargs['level'] = WARNING
        self._log(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        Запись в лог типа ERROR
        """
        kwargs['level'] = ERROR
        self._log(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Запись в лог типа CRITICAL
        """
        kwargs['level'] = CRITICAL
        self._log(msg, *args, **kwargs)
