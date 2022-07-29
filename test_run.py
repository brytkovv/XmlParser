import unittest
from run import *


class Tt:
    def __init__(self):
        self.text = 'abc'


t = Tt()


class TestRun(unittest.TestCase):

    # file testing

    def test_file_existing(self):
        self.assertRaises(TypeError, Transformator._file_existing, 1)
        self.assertRaises(TypeError, Transformator._file_existing, True)
        self.assertRaises(TypeError, Transformator._file_existing, [1, 2.3, False])
        self.assertRaises(FileNotFoundError, Transformator._file_existing, 'abd')
        self.assertEqual(Transformator._file_existing('C:\environments\Hlynov\Задание.xml'), True)
        self.assertRaises(FileNotFoundError, Transformator._file_existing, 'C:\envirnments\Hlynov\Задание.xml')
        self.assertRaises(FileNotFoundError, Transformator._file_existing, 'G:\envirnments\Hlynov\Задание.xml')

    def test_file_encoding(self):
        self.assertEqual(Transformator._file_encoding('C:\environments\Hlynov\Задание.xml'), "windows-1251")
        self.assertRaises(xml.parsers.expat.ExpatError, Transformator._file_encoding,
                          'C:\environments\Hlynov\Задани.xml')
        self.assertRaises(xml.parsers.expat.ExpatError, Transformator._file_encoding,
                          'C:\environments\Hlynov\Задание.csv')

    def test_is_file_xml(self):
        self.assertEqual(Transformator._is_file_xml('C:\environments\Hlynov\Задание.xml'), True)
        self.assertRaises(TypeError, Transformator._is_file_xml, 'C:\environments\Hlynov\Задание.csv')

    # xml testing

    def test_element_has_text(self):
        self.assertEqual(Transformator._element_has_text('aa'), '')
        self.assertEqual(Transformator._element_has_text(14), '')
        self.assertEqual(Transformator._element_has_text(True), '')
        self.assertEqual(Transformator._element_has_text(5.14), '')
        self.assertEqual(Transformator._element_has_text([1, 2, 3, 4]), '')
        self.assertEqual(Transformator._element_has_text(t), 'abc')

    def test_check_date(self):
        self.assertEqual(Transformator._check_date('05.10.2020'), '10.05.2020')
        self.assertRaises(ValueError, Transformator._check_date, '')
        self.assertRaises(ValueError, Transformator._check_date, '13.13.1040')
        self.assertRaises(ValueError, Transformator._check_date, '10.13.20')
        self.assertRaises(ValueError, Transformator._check_date, 'abc')
        self.assertRaises(TypeError, Transformator._check_date, True)
        self.assertRaises(TypeError, Transformator._check_date, 10.22)

    def test_period(self):
        self.assertEqual(Transformator._period('092020'), '092020')
        self.assertEqual(Transformator._period('09a020'), False)
        self.assertEqual(Transformator._period('999999'), False)
        self.assertEqual(Transformator._period(112020), False)
        self.assertEqual(Transformator._period(True), False)
        self.assertEqual(Transformator._period('0920'), False)
        self.assertEqual(Transformator._period(1020.22), False)

    def test_total(self):
        self.assertEqual(Transformator._total('-100.25'), False)
        self.assertEqual(Transformator._total('100.25'), '100.25')
        self.assertEqual(Transformator._total('100'), '100')
        self.assertEqual(Transformator._total('25'), '25')
        self.assertEqual(Transformator._total('100.250'), False)
        self.assertEqual(Transformator._total('100.2'), False)
        self.assertEqual(Transformator._total(True), False)
        self.assertEqual(Transformator._total(''), '')
        self.assertEqual(Transformator._total([100.00]), False)
        self.assertEqual(Transformator._total('0'), '0')
