#!/usr/bin/env python
# encoding: utf-8

from .validators import validate_domain, validate_mid
from .exceptions import Invalid
from jsonschema import validate as validate_schema, ValidationError


class Domain(object):
    """
    Representation of domain
    """

    # Json schema
    SCHEMA = {
        "description": "schema for a domain entry",
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 0},
            "name": {"type": "string"},
            "member": {"type": "integer", "minimum": 0},
            "dns_services": {"type": "boolean"}
                       },
        "required": ["name", "dns_services", "member"]
    }

    def __init__(self, name=None, member=None, dns_services=False):
        self.name = name
        self.member = member
        self.dns_services = dns_services

    def validate(self):
        """
        Validate this object
        """
        validate_domain(self.name)
        validate_mid(self.member)

    def importJSON(self, data):
        """
        Import data from JSON dict
        """
        try:
            validate_schema(data, self.SCHEMA)
        except ValidationError as e:
            raise Invalid(e.message)
        self.name = data['name']
        self.dns_services = bool(data['dns_services'])
        if 'member' in data:
            self.member = data['member']

    def as_json(self):
        """
        Return this as JSON dict
        """
        return {'name': self.name, 'id': self.id, 'member': self.member,
                'dns_services': self.dns_services
                }

    def save(self):
        """
        Save or update this object to database
        """
        self.validate()
        # Fake saving
        self.id = 0
        pass
