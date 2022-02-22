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

# THINKABOUT
- for ranges we include the max specifier, i.e. [:4]
  parses input 4, maybe allow up to 3 would be more expected?
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
    def from_state(parser, query, start):
        return ParseException('Expected %s. Query: %s. Index: %s' % (parser, query, start))


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
        r, s = self._parse(query, 0)
        if s != len(query):
            raise ParseException('Remaining query after parsing: %s' % query[s:])
        return r


class Literal(_Parser):
    """Create a parser that parses a constant string
    """
    def __init__(self, lit):
        self._lit = lit

    def _parse(self, query, start):
        if query.startswith(self._lit, start):
            return self._lit, start + len(self._lit)
        raise ParseException.from_state(self, query, start)

    def __str__(self):
        return self._lit


class Regex(_Parser):
    """Create a parser that parses a set of strings defined by the
    provided regex
    """
    def __init__(self, regex):
        self._regex = re.compile(regex)

    def _parse(self, query, start):
        match = self._regex.match(query, start)
        if not match:
            raise ParseException.from_state(self, query, start)

        r = match.group(0)
        s = start + len(r)
        if self._regex.groups == 0:
            return r, s
        return [g for g in match.groups()], s

    def __str__(self):
        return '/%s/' % self._regex.pattern


class Id(_Parser):
    def __init__(self, parser):
        self._p = Literal(parser) if isinstance(parser, str) else parser

    def _parse(self, query, start):
        return self._p._parse(query, start)

    def __str__(self):
        return str(self._p)


class Map(_Parser):
    def __init__(self, p, fn):
        self._p = p
        self._fn = fn

    def _parse(self, query, start):
        r, s = self._p._parse(query, start)
        return self._fn(r), s

    def __str__(self):
        return str(self._p)


class Drop(_Parser):
    def __init__(self, parser):
        self._p = Literal(parser) if isinstance(parser, str) else parser

    def _parse(self, query, start):
        return None, self._p._parse(query, start)[1]

    def __str__(self):
        return str(self._p)


class Repeat(_Parser):
    def __init__(self, parser, start, stop):
        self._p = parser
        self._start = start or 0
        self._stop = stop

        if self._start < 0:
            raise ValueError('start index < 0')
        if self._stop is not None and self._stop < self._start:
            raise ValueError('stop index < start index')

    def _parse(self, query, start):
        s = start  # Continue here!
        rs = []
        if self._start > 0:
            for i in range(0, self._start):
                try:
                    r, s = self._p._parse(query, s)
                    rs.append(r)
                except ParseException:
                    raise ParseException('Expected at least %s repetitions of %s'
                                         % (self._start, self._p))

        try:
            if self._stop is not None:
                for i in range(0, self._stop - self._start):
                    r, s = self._p._parse(query, s)
                    rs.append(r)
            else:
                while True:
                    r, s = self._p._parse(query, s)
                    rs.append(r)
        except ParseException:
            pass

        return rs, s

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

    def _parse(self, query, start):
        s = start
        rs = []
        for p in self._ps:
            r, s = p._parse(query, s)
            if r is not None:
                rs.append(r)
        return rs, s

    def __str__(self):
        ' + '.join(self._ps)


class Union(_Parser):
    def __init__(self, ps):
        self._ps = ps

    def _parse(self, query, start):
        for p in self._ps:
            try:
                return p._parse(query, start)
            except ParseException:
                pass

        raise ParseException.from_state(self, query, start)

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
    return Nth(lsep + ptoken + rsep, 0)
