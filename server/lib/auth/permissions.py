# encoding: utf-8

PERMISSIONS = []

def register_permission(name):
    if name not in PERMISSIONS:
        PERMISSIONS.append(name)
