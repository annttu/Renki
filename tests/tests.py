#!/usr/bin/env python
# encoding: utf-8

import unittest

import sys
import os

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, thisdir)

# Import all test modules

from test_dummyservices import TestDummyServices
from test_domains import TestDomains, TestDomain

if __name__ == '__main__':
    unittest.main()
