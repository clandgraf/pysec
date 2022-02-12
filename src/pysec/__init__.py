

class ParseException(Exception):
    pass


class _Parser(object):
    def __add__(self, p):
        ps1 = self._ps if isinstance(self, Concatenate) else [self]
        ps2 = p._ps if isinstance(p, Concatenate) else [p]
        return Concatenate(ps1 + ps2)


class Literal(_Parser):
    def __init__(self, lit):
        self._lit = lit

    def parse(self, query):
        if query.startswith(self._lit):
            return self._lit, query[len(self._lit):]
        raise ParseException('Expected %s. Query: %s' % (self._lit, query))


class Drop(_Parser):
    def __init__(self, p):
        self._p = p

    def parse(self, query):
        return None, self._p.parse(query)[1]


class Concatenate(_Parser):
    def __init__(self, ps):
        self._ps = ps

    def parse(self, query):
        q = query
        res = []
        for p in self._ps:
            r, q = p.parse(p)
            if r is not None:
                res.append(r)
        return res, q
