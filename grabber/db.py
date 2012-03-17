#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from config import Config
from logger import Logger
import MySQLdb
import sys

class DB(object):
    _conf   = None
    _log    = None
    _conn   = None
    _cursor = None

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
        else:
            return self._cursor.lastrowid
