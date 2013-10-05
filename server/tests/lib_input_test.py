# encoding: utf-8


import unittest
from lib.input import InputParser, StringValidator, IntegerValidator, \
    DomainValidator
from lib.exceptions import Invalid


class SimpleInput(InputParser):
    name = StringValidator('name')
    number = IntegerValidator('number')


class AnotherInput(SimpleInput):
    userid = IntegerValidator('userid')

class TestSimpleInput(unittest.TestCase):
    def test_valid_input(self):
        inp = {'name': 'abc', 'number': 1}
        try:
            d = SimpleInput.parse(inp)
        except Invalid:
            self.fail('Valid input should not raise "Invalid" exception')
        self.assertEqual(d['name'], 'abc', 'Failed to parse name field')
        self.assertEqual(d['number'], 1, 'Failed to parse number field')

    def test_invalid_input(self):
        inp = {'name': 'abc', 'number': 'abc'}
        with self.assertRaises(Invalid):
            SimpleInput.parse(inp)


class TestSubclassedInput(unittest.TestCase):
    def test_valid_input(self):
        inp = {'name': 'abc', 'number': 1, 'userid': 2}
        try:
            d = AnotherInput.parse(inp)
        except Invalid:
            self.fail('Valid input should not raise "Invalid" exception')
        self.assertEqual(d['name'], 'abc', 'Failed to parse name field')
        self.assertEqual(d['number'], 1, 'Failed to parse number field')
        self.assertEqual(d['userid'], 2, 'Failed to parser userid field')

class TestStringValidator(unittest.TestCase):

    def setUp(self):
        self.p = StringValidator('name')

    def test_init(self):
        self.assertEqual(self.p.name, 'name')
        self.assertFalse(self.p.permit_empty)
        self.assertEqual(self.p.default, None)
        self.assertTrue(self.p.required)

    def test_valid_input(self):
        try:
            self.p.validate('a')
        except Invalid:
            self.fail('Valid input to StringValidator should not raise "Invalid" exception')

        try:
            self.p.validate('a' * 100000)
        except Invalid:
            self.fail('Valid input to StringValidator should not raise "Invalid" exception')

        try:
            self.p.validate('123')
        except Invalid:
            self.fail('Valid input to should not raise "Invalid" exception')

    def test_invalid_input(self):
        with self.assertRaises(Invalid):
            self.p.validate('')

        with self.assertRaises(Invalid):
            self.p.validate(None)

        with self.assertRaises(Invalid):
            self.p.validate(1)

        with self.assertRaises(Invalid):
            self.p.validate(type)

    def test_permit_empty(self):
        self.p = StringValidator('name', permit_empty=True)
        self.assertTrue(self.p.permit_empty)

        try:
            self.p.validate('')
        except Invalid:
            self.fail('Valid input to should not raise "Invalid" exception')

        try:
            self.p.validate(None)
        except Invalid:
            self.fail('Valid input to should not raise "Invalid" exception')

    def test_default(self):
        self.p = StringValidator('name', default='kapsi')
        self.assertEqual(self.p.default, 'kapsi')


    def test_length(self):
        self.p = StringValidator('name', length=10)
        try:
            self.p.validate('a')
        except Invalid:
            self.fail('Valid input should not raise "Invalid" exception')

        try:
            self.p.validate('a'*10)
        except Invalid:
            self.fail('Valid input should not raise "Invalid" exception')

        with self.assertRaises(Invalid):
            self.p.validate('a'*11)

        with self.assertRaises(Invalid):
            self.p.validate('a'*1000000)


class TestIntegerValidator(unittest.TestCase):

    def setUp(self):
        self.p = IntegerValidator('id')

    def test_init(self):
        self.assertEqual(self.p.name, 'id')
        self.assertEqual(self.p.default, None)
        self.assertTrue(self.p.required)

    def test_valid_input(self):
        try:
            self.p.validate(1)
        except Invalid:
            self.fail('Valid input to should not raise "Invalid" exception')

        try:
            self.p.validate(1 * 10000000)
        except Invalid:
            self.fail('Valid input to should not raise "Invalid" exception')

        try:
            self.p.validate('123')
        except Invalid:
            self.fail('Valid input to should not raise "Invalid" exception')


    def test_invalid_input(self):
        with self.assertRaises(Invalid):
            self.p.validate('')

        with self.assertRaises(Invalid):
            self.p.validate(None)

        with self.assertRaises(Invalid):
            self.p.validate('a')

        with self.assertRaises(Invalid):
            self.p.validate(type)

        with self.assertRaises(Invalid):
            self.p.validate('0xff')

    def test_positive(self):
        self.p = IntegerValidator('positive', positive=True)

        try:
            self.p.validate(0)
        except Invalid:
            self.fail('0 is positive')

        try:
            self.p.validate('0')
        except Invalid:
            self.fail('0 is positive')

        try:
            self.p.validate(123)
        except Invalid:
            self.fail('123 is positive')

        with self.assertRaises(Invalid):
            self.p.validate(-1)

        with self.assertRaises(Invalid):
            self.p.validate('0xff')

        with self.assertRaises(Invalid):
            self.p.validate('-1')

    def test_max(self):
        self.p = IntegerValidator('max', max=128)
        try:
            self.p.validate(0)
        except Invalid:
            self.fail('0 is smaller than 128')

        try:
            self.p.validate('0')
        except Invalid:
            self.fail('0 is smaller than 128')

        try:
            self.p.validate(128)
        except Invalid:
            self.fail('128 is valid if max=128')

        with self.assertRaises(Invalid):
            self.p.validate(129)

        with self.assertRaises(Invalid):
            self.p.validate(100000)

    def test_default(self):
        self.p = IntegerValidator('name', default=1)
        self.assertEqual(self.p.default, 1)


class TestDomainValidator(unittest.TestCase):

    def setUp(self):
        self.p = DomainValidator('domain')

    def test_init(self):
        self.assertEqual(self.p.name, 'domain')
        self.assertEqual(self.p.default, None)
        self.assertTrue(self.p.required)

    def test_valid_input(self):
        try:
            self.p.validate('example.com')
        except Invalid:
            self.fail('Valid input to should not raise "Invalid" exception')

        try:
            self.p.validate('yx.fi')
        except Invalid:
            self.fail('Valid input to should not raise "Invalid" exception')

        try:
            self.p.validate('asfasfasfasdfasfasdfasdfasdfasdfasdf.com')
        except Invalid:
            self.fail('Valid input to should not raise "Invalid" exception')

        try:
            self.p.validate('xn--4caaa.fi')
        except Invalid:
            self.fail('Valid input to should not raise "Invalid" exception')

    def test_invalid_input(self):
        with self.assertRaises(Invalid):
            self.p.validate('')

        with self.assertRaises(Invalid):
            self.p.validate(None)

        with self.assertRaises(Invalid):
            self.p.validate('a')

        with self.assertRaises(Invalid):
            self.p.validate(type)

        with self.assertRaises(Invalid):
            self.p.validate('.example.com')

        with self.assertRaises(Invalid):
            self.p.validate('example')

        with self.assertRaises(Invalid):
            self.p.validate('yx')

        with self.assertRaises(Invalid):
            self.p.validate('asdf')

        with self.assertRaises(Invalid):
            self.p.validate('asdf\x00.fi')


    def test_default(self):
        self.p = IntegerValidator('name', default=1)
        self.assertEqual(self.p.default, 1)



if __name__ == '__main__':
    unittest.main()
