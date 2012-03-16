#! /usr/bin/env python
# -*- coding: utf-8 -*-
#vim: set syntax=python

from ConfigParser import RawConfigParser

class Singleton(type):
    def __init__(cls, *args, **kw):
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance


class Config(object):
    __metaclass__   = Singleton

    def __init__(self, configPath):
        Config._conf = RawConfigParser()
        Config._conf.read(configPath)

    def __getattr__(self, attr):
        return getattr(Config._conf, attr)

    def __setattr__(self, attr, value):
        return setattr(Config._conf, attr, value)
