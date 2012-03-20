#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from config import Config
from logger import Logger
import MySQLdb
import sys
from traceback import extract_tb, format_list

DISABLED_RESOURCE   = 0
ENABLED_RESOURCE    = 1

class Singleton(type):
    def __init__(cls, *params, **kw):
        cls.instance = None

    def __call__(cls, *params, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*params, **kw)
        return cls.instance

class DB(object):
    __metaclass__   = Singleton
    _conf           = None
    _log            = None
    _conn           = None
    _cursor         = None

    def __init__(self):
        self._conf = Config()
        self._log = Logger()
        self._connect()

    def __del__(self):
        if isinstance(self._conn, MySQLdb.connections.Connection):
            self._conn.commit()
            self._cursor.close()
            self._conn.close()

    def _connect(self):
        if self._conn is None:
            try:
                self._conn = MySQLdb.connect(
                    host = self._conf.get('db', 'host'),
                    user = self._conf.get('db', 'user'),
                    passwd = self._conf.get('db', 'pass'),
                    db = self._conf.get('db', 'db'),
                    charset = self._conf.get('db', 'encode')
                )
                self._cursor = self._conn.cursor()
            except Exception, ex:
                self._log.critical('Ошибка соединения с БД', exc_info=True)
                sys.exit(ex)
            else:
                self._log.debug('Создано соединение с БД')

    @property
    def cursor(self):
        return self._cursor

    def execute(self, query, *params, **kw):
        try:
            self._cursor.execute(query, params)
            if self._cursor._warnings:
                self._log.critical('warning detected!')
                sys.exit('Warning detected!')
        except (MySQLdb.Error, MySQLdb.IntegrityError), e:
            self._log.critical('Mysql runtime error %d: %s', e.args[0], e.args[1])
            sys.exit(e.args[1])
        except (TypeError,), e:
            self._log.debug('trace:\n%s', '\n'.join(format_list(extract_tb(sys.exc_info()[2]))))
            self._log.critical('Ошибка формирования запроса из шаблона: %s', e)
            sys.exit(e)
        else:
            return self._cursor.lastrowid
