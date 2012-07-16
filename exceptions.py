#!/usr/bin/env python
# encoding: utf-8
"""
exceptions.py
"""

class DatabaseError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % self.value

class DoesNotExist(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % self.value

class PermissionDenied(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % self.value
        
class AlreadyExist(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % self.value