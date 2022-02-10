import unittest
import back

class TestMethods(unittest.TestCase):

    def test_1(self):
        self.assertEqual(back.date_standrt('2022-2-15'), '2022-02-15')

if __name__ == '__main__':
    unittest.main()

