#!/usr/bin/env python
from pyparsing import Combine, Word, Literal, Optional, oneOf, Group, ZeroOrMore, Suppress, quotedString, removeQuotes, alphanums, nums, alphas, ParseResults
from collections import namedtuple

class InvalidFieldException(Exception):
  pass

class InvalidOperatorException(Exception):
  pass

class InvalidValueException(Exception):
  pass

def parse_add(*args, **kwargs):
    op = kwargs.get("op", "and")
    x = args[0]
    for y in args[1:]:
        x = x + ParseResults(op) + y
    return ParseResults(x)

def parse_join(x, op="and"):
    result = [op] * (len(x) * 2 - 1)
    result[0::2] = x
    return ParseResults(result)


class FilterParser(object):
  def __init__(self):
    self.__grammar()

  def __grammar(self):
    """
    Pyparsing grammar to parse the filter string.
    """

    float_ = Combine(Word(nums) + Literal(".") + Word(nums)).setParseAction(lambda x,y,z: float(z[0]))
    sci = Combine(Word(nums) + Optional(".") + Optional(Word(nums)) + oneOf("e E") + Optional("-") + Word(nums)).setParseAction(lambda x,y,z: float(z[0]))
    int_ = Word(nums).setParseAction(lambda x,y,z: int(z[0]))

    comp = oneOf("in eq gt lt ge le < > = like",caseless=True).setResultsName("comp")
    op = oneOf("and or",caseless=True).setResultsName("op")

    lhs = Word(alphanums+"_").setResultsName("lhs")
    element = sci | float_ | int_ | quotedString.setParseAction(removeQuotes) | Word(alphanums)
    rhs = (element + ZeroOrMore(Suppress(",") + element)).setResultsName("rhs")

    stmt = Group(
      lhs + comp + rhs
    ).setResultsName("statement")

    expr = stmt + ZeroOrMore(op + stmt)

    self.grammar = expr

  def StatementLiteral(self, lhs, comp, rhs):
    return ParseResults(lhs, "lhs", False)  + \
        ParseResults(comp, "comp", False) + \
        ParseResults([rhs], "rhs", True)

  def parse(self,query):
    matches = self.grammar.parseString(query)
    for match in matches:
      yield match

  def statements(self,query):
    """
    Returns only the statements from a filter string.

    Example:

      In [1]: from uriparsing import *

      In [2]: foo = FilterParser()

      In [3]: foo.statements("source = 42 and gene_id = 'ENSG1'")
      Out[3]:
      {'gene_id': Statement(field='gene_id', comp='=', value='ENSG1'),
       'source': Statement(field='source', comp='=', value=42)}

      In [4]: foo.statements("source = 42 and gene_id = 'ENSG1'").get("source").value
      Out[4]: 42

      In [5]: foo.statements("source in 42, 43, 44 and gene_id = 'ENSG1'").get("source").value
      Out[5]: [42, 43, 44]

    Args:
      query: Filter string

    Returns:
      dict: Mapping from lhs --> statement, where statement is an object having
        3 attributes: field, comp, value
    """

    if query is not None:
      matches = self.grammar.parseString(query)
    else:
      return

    params = {}
    Statement = namedtuple("Statement","field comp value".split())

    for match in matches:
      if isinstance(match,str):
        # This would be "AND", "OR", etc.
        # But we're just looking for statements, so just keep going.
        pass
      else:
        lhs = match.lhs
        comp = match.comp

        if comp == "in":
          rhs = list(match.rhs)
        else:
          rhs = list(match.rhs)[0]

        params[lhs] = Statement(lhs,comp,rhs)

    return params

  def find_genome_range(self, x):
    """Find chr,start,stop from a parsed filter"""
    chrom = None
    left = None
    open_left = False
    right = None
    open_right = False
    uncaught =  []
    for m in x:
      if isinstance(m, basestring):
        if m == "and":
          continue
        else:
          raise Exception("Unable to handle '{}' conjunction".format(m))
      field = m[0]
      op = m[1]
      val = m[2]
      if field == "chromosome":
        if op == "eq":
          chrom = val
        else:
          raise Exception("Unable to parse operator '{}' for chrom".format(op))
      elif field == "position":
        if op == "gt" or op == "ge" or op==">":
          left = val
          open_left = op != "ge" 
        elif op == "lt" or op =="le" or op=="<":
          right = val
          open_right = op != "le" 
        elif op == "eq":
          left = val
          right = val
        else:
          raise Exception("Unable to parse operator '{}' for position".format(op))
      else:
          uncaught.append(m)
    resp= {"chrom": chrom, "left": left, "right": right,
      "open_left": open_left, "open_right": open_right}
    if chrom is None or left is None or right is None:
      raise Exception("Unable to find bounded range")
    return resp, parse_join(uncaught)

  def left_middle_right(self, matches):
    """return filters for left, middle and right of genomic range"""
    genome_range, other_filter = self.find_genome_range(matches)

    chrom = self.StatementLiteral("chromosome", "eq", genome_range["chrom"])
    ex_left = self.StatementLiteral("position", "le", genome_range["left"])
    ex_right = self.StatementLiteral("position", "ge", genome_range["right"])

    left_filter = parse_add(parse_join([chrom, ex_left]), other_filter)
    right_filter = parse_add(parse_join([chrom, ex_right]), other_filter)

    in_left = self.StatementLiteral("position", "ge", genome_range["left"])
    in_right = self.StatementLiteral("position", "lt", genome_range["right"])
    middle_filter = parse_add(parse_join([chrom, in_right, in_left]), other_filter)
    return {"left": left_filter, "right": right_filter, "middle": middle_filter, \
      "range": genome_range}

  @staticmethod
  def _tests():
    grammar_tests = [
      "analysis in 3, 4 and chromosome eq 10 and start gt 10 and end lt 10000",
      "analysis in 1 and chromosome in 20, 22 and start gt 1 and end le 20",
      "analysis in 5, 6",
      "some_field eq '20' and another_field eq 99",
      "id gt 3 and pval lt 5.341e-14",
      "analysis in 3 and chromosome in 'chrX','chrY' and start gt 5000",
      "thresholds in 3.7, 4.6, 5.2 and chromsome eq 20",
      "analysis in 3,4 and start > 42 and end < 800",
      "reference eq 1 and chromosome2 eq '9'",
      "reference eq 1 and chromosome2 eq '9' and position2 ge 16961 and position2 le 16967",
      "reference eq 1 and chromosome2 eq '9' and position2 ge 16961 and position2 le 16967 and variant1 eq '9:16918_G/C'",
      "source in 1 and gene_name like 'TCF*'"
    ]

    fp = FilterParser()
    for t in grammar_tests:
      print t
      for m in fp.parse(t):
        if isinstance(m,str):
          print m
        else:
          print m.lhs, m.comp, m.rhs

      print "\n"

class LDAPITranslator(object):
  def __init__(self):
    self.filter_parser = FilterParser()

  def to_refsnp_url(self,query):
    """
    Convert a query string into a suitable URL for requesting refsnp LD from the API server
    running locally.

    This really only translates correctly for refsnp LD queries. If you give a generic query,
    it will likely error.

    Therefore, only the following fields should be used:
      chromosome2
      position2
      variant1
      reference

    Args:
      query: the filter string submitted via the API request

    Returns:
      string: URL constructed from the filter string
      dict: field -> [(operator,value)]
        List is necessary because a field can be specified multiple times, e.g. position2 le 10 and position2 ge 1
    """

    # filter: reference eq 1 and chromosome2 eq '9' and position2 ge 16961 and position2 le 16967 and variant1 eq '9:16918_G/C'
    # fields: chr,pos,rsquare

    # http://portaldev.sph.umich.edu/api_ld/ld?population=ALL & chromosome=2 & variant=2:167604192_A/G & startbp=167604192 & endbp=168104192

    ops = {
      "gt": ">",
      "ge": ">=",
      "le": "<=",
      "lt": "<",
      "eq": "=",
      "in": "IN",
      "=": "=",
      ">": ">",
      "<": "<"
    }

    reference_to_code = {
      1 : "ALL",
      2 : "EUR"
    }

    acceptable_fields = [
      "population",
      "reference",
      "chromosome1",
      "chromosome2",
      "position1",
      "position2",
      "variant1",
      "variant2"
    ]

    if query is not None:
      matches = self.filter_parser.grammar.parseString(query)
    else:
      matches = []

    url = []
    parsed = {}
    for match in matches:
      if isinstance(match,str):
        if match == 'and':
          pass
        elif match == 'or':
          raise NotImplementedError, "'OR' not implemented"
      else:
        if match.lhs not in acceptable_fields:
          raise InvalidFieldException, "Invalid field in query string: {}".format(match.lhs)

        if match.comp not in ops:
          raise InvalidOperatorException, "Invalid operator in query string: {}".format(match.comp)

        rhs = list(match.rhs)
        if match.comp == "in":
          if len(rhs) > 1:
            raise InvalidValueException, "This endpoint only supports 1 value per right-hand side"
        elif match.comp == "eq":
          pass

        v_rhs = rhs[0]
        v_lhs = match.lhs

        # Need to store for return, but we need the values before translation to the LD API.
        parsed.setdefault(v_lhs,{}).setdefault(match.comp,[]).append(v_rhs)

        # Handle reference. The LD server expects "ALL" or "EUR", we receive 1, 2, etc.
        if v_lhs == "reference":
          panel = reference_to_code.get(v_rhs)
          if panel is None:
            raise InvalidValueException, "Reference panel ID given ({}) is not valid".format(v_rhs)

          v_lhs = "population"
          v_rhs = panel

        # Chromosome2 is just the chromosome
        elif v_lhs == "chromosome2":
          v_lhs = "chromosome"

        # position2 > v becomes startbp = v
        # position2 < v becomes endbp = v
        elif v_lhs == "position2":
          if match.comp in ("ge","gt"):
            v_lhs = "startbp"
          elif match.comp in ("le","lt"):
            v_lhs = "endbp"

        elif v_lhs == "variant1":
          v_lhs = "variant"

        url.append("{}={}".format(v_lhs,v_rhs))

    return "&".join(url), parsed

class SQLCompiler(object):
  def __init__(self):
    self.filter_parser = FilterParser()
    self.ops = {
      "gt": ">",
      "ge": ">=",
      "le": "<=",
      "lt": "<",
      "eq": "=",
      "not": "<>",
      "in": "IN",
      "=": "=",
      ">": ">",
      "<": "<",
      'like': 'like'
    }
    # If these appear in the SQL string, they need to be quoted.
    self.sql_keywords = [
      "end"
    ]

  def quote_keywords(self, x):
    if x in self.sql_keywords:
      return '"{}"'.format(x)
    else:
      return x

  def _to_where(self, terms, acceptable_fields, field_to_col=None):
    where = []
    params = {}
    pcount = 1

    if terms is None or len(terms)<1:
      return where, params

    where.append("WHERE")

    for term in terms:
      if isinstance(term,str):
        if term == 'and':
          where.append("AND")
        elif term == 'or':
          where.append("OR")
      else:
        lhs = field_to_col.get(term.lhs,term.lhs) if field_to_col is not None else term.lhs
        if lhs not in acceptable_fields:
          raise InvalidFieldException, "Invalid field in query string: {}".format(term.lhs)

        where.append(self.quote_keywords(lhs))

        sql_comp = self.ops.get(term.comp)
        if sql_comp is None:
          raise InvalidOperatorException, "Invalid operator in query string: {}".format(term.comp)
        where.append(sql_comp)

        if term.comp == "in":
          rhs = list(term.rhs)
        else:
          rhs = list(term.rhs)[0]

        if term.comp == "like":
          rhs = rhs.replace("*","%")

        mparam = "p{}".format(pcount)
        if isinstance(rhs,list):
          params[mparam] = tuple(rhs)
          where.append(":{}".format(mparam))
        else:
          params[mparam] = rhs
          where.append(":{}".format(mparam))

        pcount += 1
    return where, params

  def to_sql(self, query, table, acceptable_fields, columns=None, sort_columns=None, field_to_col=None, limit=None):
    if query is not None:
      terms = self.filter_parser.grammar.parseString(query)
    else:
      terms = []
    return self.to_sql_parsed(terms, table, acceptable_fields, columns, sort_columns, field_to_col, limit)

  def to_sql_parsed(self, terms, table, acceptable_fields, columns=None, sort_columns=None, field_to_col=None, limit=None):
    """
    Convert an API query string into a SQL statement.

    This should only be used if:
    * Database privileges for this user are read only
    * The programmer provides the table name, NOT the user
    * The programmer provides the columns to be returned, NOT the user

    Otherwise, you will probably get SQL injected.

    Args:
      terms: the parsed filter string submitted via API request
      table: name of the table to filter against. You are assumed to have come up with
        the table name yourself, and not from user input.
      acceptable_fields: only permit queries against these field names (not optional)
      columns: which columns from the table should be returned? Assumed to come from programmer
        and NOT user input. If not provided, the query will just contain "SELECT * ..."
      sort_columns: list of columns to use in an ORDER BY clause. These should not come from user input
        (or they should be validated beforehand, like columns.)
      field_to_col: if fields in filter string need to be converted to database column names, provide a
        dictionary mapping from field --> column
    Returns:
      string: prepared SQL statement
      dict: named parameters for SQL statement (sqlalchemy format). Don't put these directly into the
        SQL string. You must use the DBAPI (sqlalchemy) to do it (or, broken record, you'll get SQL injected.)
    """

    sql = [
      "SELECT {} FROM {}".format(
        "*" if columns is None else ",".join(map(self.quote_keywords,columns)),
        table
      )
    ]

    where, params = self._to_where(terms, acceptable_fields, field_to_col)
    if len(where)>0:
      sql.extend(where)

    if sort_columns is not None:
      sql.append("ORDER BY {}".format(",".join(map(self.quote_keywords, sort_columns))))

    if limit is not None:
      sql.append("LIMIT {}".format(limit))

    return " ".join(sql), params

def uri_example():
  from sqlalchemy import text, create_engine
  engine = create_engine('postgresql://portaldev_user:portaldev_user@localhost:5433/api_internal_dev')
  con = engine.connect()
  sqlcompiler = SQLCompiler()

  sql, params = sqlcompiler.to_sql(
    "trait in 'T2D','FGlu' and chromosome > 10 and start gt 0 and end lt 4000",
    "rest.single_analyses",
    "trait chromosome start end".split()
  )
  print sql, "\n", params

  txt = text(sql)
  cur = con.execute(txt,params)
  for row in cur:
    print row
  
