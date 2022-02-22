import re

"""pysec provides entities to define recursive descent parsers inline
in code. These entities follow a technique called parser combinators,
inspired by the popular haskell module parsec.

Parsers are either terminal parsers, that recognize single tokens or
combined parsers that are constructed from other parsers.

Each Parser transforms it's input into a data structure defined by its
constituents. Parser Combinators and Token Parsers

# Defining Lexicographic Tokens

# Complex Grammars using Parser Combinators

# Reification via Parser Combinators

"""


__all__ = [
    'ParseException',
    'Literal',
    'Regex',
    'Drop',
    'Nth',
    'In',
]


class ParseException(Exception):
    def from_state(parser, query):
        return ParseException('Expected %s. Query: %s' % (parser, query))


class _Parser(object):
    def __add__(self, p):
        ps1 = self._ps if isinstance(self, Concat) else [self]
        ps2 = [Drop(p)] if isinstance(p, str) else p._ps if isinstance(p, Concat) else [p]
        return Concat(ps1 + ps2)

    def __radd__(self, p):
        ps1 = [Drop(p)] if isinstance(p, str) else p._ps if isinstance(p, Concat) else [p]
        ps2 = self._ps if isinstance(self, Concat) else [self]
        return Concat(ps1 + ps2)

    def __or__(self, p):
        ps1 = self._ps if isinstance(self, Union) else [self]
        ps2 = [Literal(p)] if isinstance(p, str) else p._ps if isinstance(p, Union) else [p]
        return Union(ps1 + ps2)

    def __ror__(self, p):
        ps1 = [Literal(p)] if isinstance(p, str) else p._ps if isinstance(p, Union) else [p]
        ps2 = self._ps if isinstance(self, Union) else [self]
        return Union(ps1 + ps2)

    def __rshift__(self, fn):
        return Map(self, fn)

    def __truediv__(self, separator):
        return Joined(self, separator)

    def __neg__(self):
        return Id(self)

    def __invert__(self):
        # Retain structure: Protect + subparsers from being merged
        return Optional(self)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return Repeat(self, i.start, i.stop)
        else:
            return Repeat(self, i, i)

    def parse(self, query):
        r, q = self._parse(query)
        if len(q) != 0:
            raise ParseException('Remaining query after parsing: %s' % q)
        return r


class Literal(_Parser):
    """Create a parser that parses a constant string
    """
    def __init__(self, lit):
        self._lit = lit

    def _parse(self, query):
        if query.startswith(self._lit):
            return self._lit, query[len(self._lit):]
        raise ParseException.from_state(self, query)

    def __str__(self):
        return self._lit


class Regex(_Parser):
    """Create a parser that parses a set of strings defined by the
    provided regex
    """
    def __init__(self, regex):
        self._regex = re.compile(regex)

    def _parse(self, query):
        match = self._regex.match(query)
        if not match:
            raise ParseException.from_state(self, query)

        r = match.group(0)
        q = query[len(r):]
        if self._regex.groups == 0:
            return r, q
        return [g for g in match.groups()], q

    def __str__(self):
        return '/%s/' % self._regex.pattern


class Id(_Parser):
    def __init__(self, p):
        self._p = p

    def _parse(self, query):
        return self._p._parse(query)

    def __str__(self):
        return str(self._p)


class Map(_Parser):
    def __init__(self, p, fn):
        self._p = p
        self._fn = fn

    def _parse(self, query):
        r, q = self._p._parse(query)
        return self._fn(r), q

    def __str__(self):
        return str(self._p)


class Drop(_Parser):
    def __init__(self, parser):
        self._p = Literal(parser) if isinstance(parser, str) else parser

    def _parse(self, query):
        return None, self._p._parse(query)[1]

    def __str__(self):
        return str(self._p)


class Repeat(_Parser):
    def __init__(self, parser, start, stop):
        if start is not None and start < 0:
            raise ValueError('start index < 0')
        if stop is not None and stop < start:
            raise ValueError('stop index < start index')
        self._p = parser
        self._start = start or 0
        self._stop = stop

    def _parse(self, query):
        rs = []
        q = query
        if self._start > 0:
            for i in range(0, self._start):
                try:
                    r, q = self._p._parse(q)
                    rs.append(r)
                except ParseException:
                    raise ParseException('Expected at least %s repetitions of %s'
                                         % (self._start, self._p))

        try:
            if self._stop is not None:
                for i in range(0, self._stop - self._start):
                    r, q = self._p._parse(q)
                    rs.append(r)
            else:
                while True:
                    r, q = self._p._parse(q)
                    rs.append(r)
        except ParseException:
            pass

        return rs, q

    def __str__(self):
        if self._stop is None:
            if self._start == 0:
                return "%s*" % self._p
            if self._start == 1:
                return "%s+" % self._p

        return "%s{%d:%d}" % (self._p, self._start, self._stop)


class Concat(_Parser):
    def __init__(self, ps):
        self._ps = ps

    def _parse(self, query):
        q = query
        res = []
        for p in self._ps:
            r, q = p._parse(q)
            if r is not None:
                res.append(r)
        return res, q

    def __str__(self):
        ' + '.join(self._ps)


class Union(_Parser):
    def __init__(self, ps):
        self._ps = ps

    def _parse(self, query):
        for p in self._ps:
            try:
                return p._parse(query)
            except ParseException:
                pass

        raise ParseException.from_state(self, query)

    def __str__(self):
        ' | '.join(self._ps)


def Nth(pToken, i):
    return pToken \
        >> (lambda res: res[i] if i < len(res) else None)


def Joined(pToken, pSeparator):
    return (-pToken + Nth(Drop(pSeparator) + -pToken, 0)[:]) \
        >> (lambda rs: [rs[0], *rs[1]])


def Optional(pToken):
    return Nth(pToken[0:1], 0)


def In(lsep, ptoken, rsep):
    return Nth('[' + ptoken + ']', 0)
