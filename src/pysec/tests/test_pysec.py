
import pysec
import unittest


class TestLiteral(unittest.TestCase):
    def setUp(self):
        self.literal = pysec.Literal('hello')

    def test_parse_success(self):
        lit = self.literal.parse('hello')
        self.assertEqual(lit, 'hello')

    def test_parse_failure(self):
        with self.assertRaises(pysec.ParseException):
            self.literal.parse('helloworld')

    # def test_success(self):
    #     lit, rest = self.literal._parse('helloworld')
    #     self.assertEqual(lit, 'hello')

    # def test_rest(self):
    #     lit, rest = self.literal._parse('helloworld')
    #     self.assertEqual(rest, 'world')

    # def test_failure(self):
    #     with self.assertRaises(pysec.ParseException):
    #         self.literal._parse('hiworld')


class TestRegex(unittest.TestCase):
    def setUp(self):
        self.grammar_simple = pysec.Regex('[A-Za-z_][A-Za-z0-9_]*')
        self.grammar_complex = pysec.Regex(r'(\d+)\.(\d+)\.(\d+)')

    def test_success_group0(self):
        result = self.grammar_simple.parse('foobah1')
        self.assertEqual(result, 'foobah1')

    def test_failure_group0(self):
        with self.assertRaises(pysec.ParseException):
            self.grammar_simple.parse('1foobah')

    def test_success_groups(self):
        result = self.grammar_complex.parse('15.3.0')
        self.assertEqual(result, ['15', '3', '0'])

    def test_failure_groups(self):
        with self.assertRaises(pysec.ParseException):
            self.grammar_complex.parse('1foobah')


class TestConcatDropsLiteral(unittest.TestCase):
    def setUp(self):
        g0 = pysec.Regex('[A-Za-z_][A-Za-z0-9_]*')
        g1 = pysec.Regex(r'(\d+)\.(\d+)\.(\d+)')
        self.grammar = g1 + '-' + g0

    def test_success(self):
        result = self.grammar.parse('15.3.0-beta1')
        self.assertEqual(result, [['15', '3', '0'], 'beta1'])


class TestConcatReifies(unittest.TestCase):
    def setUp(self):
        g0 = pysec.Regex('[A-Za-z_][A-Za-z0-9_]*')
        g1 = pysec.Regex(r'(\d+)\.(\d+)\.(\d+)')
        self.grammar = g1 + '-' + g0

    def test_success(self):
        result = self.grammar.parse('15.3.0-beta1')
        self.assertEqual(result, [['15', '3', '0'], 'beta1'])


class TestConcatRand(unittest.TestCase):
    def setUp(self):
        g0 = pysec.Regex('[A-Za-z_][A-Za-z0-9_]*')
        self.grammar = '-' + g0

    def test_success(self):
        result = self.grammar.parse('-beta1')
        self.assertEqual(result, ['beta1'])


class TestUnion(unittest.TestCase):
    def setUp(self):
        g0 = pysec.Regex('[A-Za-z_][A-Za-z0-9_]*')
        g1 = pysec.Regex(r'(\d+)\.(\d+)\.(\d+)')
        self.grammar = g0 | g1

    def test_success_first_opt(self):
        result = self.grammar.parse('beta1')
        self.assertEqual(result, 'beta1')

    def test_success_second_opt(self):
        result = self.grammar.parse('15.3.0')
        self.assertEqual(result, ['15', '3', '0'])


class TestUnionRor(unittest.TestCase):
    def setUp(self):
        g1 = pysec.Regex(r'(\d+)\.(\d+)\.(\d+)')
        self.grammar = 'foo' | g1

    def test_success_first_opt(self):
        result = self.grammar.parse('foo')
        self.assertEqual(result, 'foo')

    def test_success_second_opt(self):
        result = self.grammar.parse('15.3.0')
        self.assertEqual(result, ['15', '3', '0'])


class TestMap(unittest.TestCase):
    def setUp(self):
        self.grammar = pysec.Regex(r'(\d+)\.(\d+)\.(\d+)') \
            >> (lambda ds: list(map(int, ds)))

    def test_success_second_opt(self):
        result = self.grammar.parse('15.3.0')
        self.assertEqual(result, [15, 3, 0])


class TestSelectorGrammar(unittest.TestCase):
    def setUp(self):
        Identifier = pysec.Regex('[A-Za-z_][A-Za-z0-9_]*')
        Value = pysec.Regex('[A-Za-z0-9_\\.]*')
        FilterParam = Identifier + '=' + Value
        Filter = (FilterParam / ',') \
            >> (lambda res: {k: v for k, v in res})
        Selector = Identifier + ~pysec.In('[', Filter, ']') \
            >> (lambda res: {'entity': res[0],
                             'filter': None if len(res) < 2 else res[1]})
        Query = (Selector / '.')

        self.grammar = Query

    def test_success(self):
        result = self.grammar.parse('product_instance[produktname=cs.web,version=15.5.2].FixedErrors')
        self.assertEqual(result, [{'entity': 'product_instance',
                                   'filter': {'produktname': 'cs.web', 'version': '15.5.2'}},
                                  {'entity': 'FixedErrors',
                                   'filter': None}])


if __name__ == '__main__':
    unittest.main()
