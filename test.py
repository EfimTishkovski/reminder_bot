import unittest
import back

class TestMethods(unittest.TestCase):

    def test_1(self):
        self.assertEqual(back.date_standrt('2022.2.15'), '2022.02.15')

    def test_time(self):
        self.assertEqual(back.time_standart('9:17'), '09:17')
        self.assertEqual(back.time_standart('09:7'), '09:07')
        self.assertEqual(back.time_standart('4:6'), '04:06')
        self.assertEqual(back.time_standart('08:16'), '08:16')
        self.assertEqual(back.time_standart('14:58'), '14:58')

    def test_2(self):
        self.assertEqual(back.check_date('10.15.2022')[0], False)
        self.assertEqual(back.check_date('15.02.2022')[0], True)
        self.assertEqual(back.check_date('11.12.2022')[0], True)
        self.assertEqual(back.check_date('15.13.2022')[0], False)
        self.assertEqual(back.check_date('35.11.2022')[0], False)
        self.assertEqual(back.check_date('45.18.2022')[0], False)
        self.assertEqual(back.check_date('15-13-2022')[0], False)

    def test_3(self):
        self.assertEqual(back.check_time('12:40')[0], True)
        self.assertEqual(back.check_time('24:40')[0], False)
        self.assertEqual(back.check_time('5:70')[0], False)
        self.assertEqual(back.check_time('25:70')[0], False)
        self.assertEqual(back.check_time('7-40')[0], False)

if __name__ == '__main__':
    unittest.main()

