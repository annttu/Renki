#!/usr/bin/env python
# encoding: utf-8

import unittest


# Testing modules to run
tests = ['test_generic']


def is_wanted_test(name, class_):
    if type(class_) != type(unittest.TestCase):
        return False
    if 'BaseRoutesTest' in name:
        return False
    elif not issubclass(class_, unittest.TestCase):
        return False
    return True


def load_tests():
    suite = unittest.TestSuite()
    testloader = unittest.TestLoader()
    for test in tests:
        test_module = __import__(test, fromlist=['tests'])
        for i in vars(test_module):
            if not is_wanted_test(i, vars(test_module)[i]):
                continue
            suite.addTests(testloader.loadTestsFromName(i,
                           module=test_module))

        #loaded_tests = testloader.loadTestsFromModule(test_module)
        #print("TESTS: %s" % dir(loaded_tests))
        #suite.addTests(loaded_tests)
    return suite

if __name__ == '__main__':
    testsuite = load_tests()
    unittest.TextTestRunner(verbosity=2).run(testsuite)
