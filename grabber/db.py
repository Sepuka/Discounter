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

class DB(object):
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
                self._log.critical('Ошибка соединения с БД', exc_info=True, moduleName=self.__class__.__name__)
                sys.exit(ex)
            else:
                self._log.debug('Создано соединение с БД', moduleName=self.__class__.__name__)

    @property
    def cursor(self):
        return self._cursor

    def execute(self, query, *params, **kw):
        try:
            self._cursor.execute(query, params)
            if self._cursor._warnings:
                self._log.warning('warning detected!', moduleName=self.__class__.__name__)
                wquery = """SHOW WARNINGS"""
                self.execute(wquery)
                for warning in self.cursor.fetchall():
                    self._log.warning('WARNING: "%s" in query "%s"', warning[2], query, moduleName=self.__class__.__name__)
        except (MySQLdb.Error, MySQLdb.IntegrityError), e:
            self._log.critical('Mysql runtime error %d: %s', e.args[0], e.args[1], moduleName=self.__class__.__name__)
            raise
        except (TypeError,), e:
            self._log.debug('trace:\n%s', '\n'.join(format_list(extract_tb(sys.exc_info()[2]))))
            self._log.critical('Ошибка формирования запроса из шаблона: %s', e, moduleName=self.__class__.__name__)
            sys.exit(e)
        else:
            return self._cursor.lastrowid
