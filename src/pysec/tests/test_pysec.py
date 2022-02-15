
import pysec
import unittest

# Identifier = Regex('[A-Za-z_][A-Za-z0-9_]*')
# Value = Regex('[A-Za-z0-9_\\.]*')
# FilterParam = Identifier + '=' + Value
# Filter = (FilterParam / ',') \
#     >> (lambda res: {k: v for k, v in res})
# Selector = Identifier + ~In('[', Filter, ']') \
#     >> (lambda res: {'entity': res[0],
#                      'filter': None if len(res) < 2 else res[1]})
# Query = (Selector / '.')

# Query.parse('product_instance[produktname=cs.web,version=15.5.2].FixedErrors')

class TestLiteral(unittest.TestCase):
    def setUp(self):
        self.literal = pysec.Literal('hello')

    def test_parse_success(self):
        lit = self.literal.parse('hello')
        self.assertEqual(lit, 'hello')

    def test_parse_failure(self):
        with self.assertRaises(pysec.ParseException):
            self.literal.parse('helloworld')

    def test_success(self):
        lit, rest = self.literal._parse('helloworld')
        self.assertEqual(lit, 'hello')

    def test_rest(self):
        lit, rest = self.literal._parse('helloworld')
        self.assertEqual(rest, 'world')

    def test_failure(self):
        with self.assertRaises(pysec.ParseException):
            self.literal._parse('hiworld')

if __name__ == '__main__':
    unittest.main()
