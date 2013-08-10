#!/usr/bin/env python
# encoding: utf-8

OK_STATUS = 'OK'
ERROR_STATUS = 'ERROR'
STATUS_CODES = [OK_STATUS, ERROR_STATUS]


def ok(data={}):
    """
    Creates uniform return values for bottle routes

    @param data: Data fields
    @type data: dict
    """
    if not data:
        data = {}
    data['status'] = OK_STATUS
    return data


def error(error, data={}):
    """
    Creates uniform return values for failed api querys

    @param error: Error message
    @type error: string
    @param data: Other data
    @type data: dict
    """
    if not data:
        data = {}
    data['status'] = ERROR_STATUS
    data['error'] = error
    return data
