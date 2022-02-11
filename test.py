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

    def test_date(self):
        self.assertTrue(back.check_date('2022.02.15'), True)
        self.assertTrue(back.check_date('2022.12.11'), True)
        self.assertTrue(back.check_date('2022.13.15'), False)

if __name__ == '__main__':
    unittest.main()

