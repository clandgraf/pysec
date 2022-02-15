
from pysec import *

Identifier = Regex('[A-Za-z_][A-Za-z0-9_]*')
Value = Regex('[A-Za-z0-9_\\.]*')
FilterParam = Identifier + '=' + Value
Filter = (FilterParam / ',') \
    >> (lambda res: {k: v for k, v in res})
Selector = Identifier + ~In('[', Filter, ']') \
    >> (lambda res: {'entity': res[0],
                     'filter': None if len(res) < 2 else res[1]})
Query = (Selector / '.')

Query.parse('product_instance[produktname=cs.web,version=15.5.2].FixedErrors')
