#!/usr/bin/env python
from pyparsing import Combine, Word, Literal, Optional, oneOf, Group, ZeroOrMore, Suppress, quotedString, removeQuotes, alphanums, nums, alphas
from collections import namedtuple

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
  "reference eq 1 and chromosome2 eq '9' and position2 ge 16961 and position2 le 16967 and variant1 eq '9:16918_G/C'"
]

class InvalidFieldException(Exception):
  pass

class InvalidOperatorException(Exception):
  pass

class InvalidValueException(Exception):
  pass

class FilterParser(object):
  def __init__(self):
    self.__grammar()

  # def _convert_rhs(self,rhs):
  #   rhs = list(rhs)
  #   if len(rhs) > 1:
  #     return rhs
  #   else:
  #     return rhs[0]

  def __grammar(self):
    """
    Pyparsing grammar to parse the filter string.
    """

    float_ = Combine(Word(nums) + Literal(".") + Word(nums)).setParseAction(lambda x,y,z: float(z[0]))
    sci = Combine(Word(nums) + Optional(".") + Optional(Word(nums)) + oneOf("e E") + Optional("-") + Word(nums)).setParseAction(lambda x,y,z: float(z[0]))
    int_ = Word(nums).setParseAction(lambda x,y,z: int(z[0]))

    comp = oneOf("in eq gt lt ge le < > =",caseless=True).setResultsName("comp")
    op = oneOf("and or",caseless=True).setResultsName("op")

    lhs = Word(alphanums+"_").setResultsName("lhs")
    element = sci | float_ | int_ | quotedString.setParseAction(removeQuotes) | Word(alphanums)
    rhs = (element + ZeroOrMore(Suppress(",") + element)).setResultsName("rhs")

    stmt = Group(
      lhs + comp + rhs
    )

    expr = stmt + ZeroOrMore(op + stmt)

    self.grammar = expr

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

    return "&".join(url)

class SQLCompiler(object):
  def __init__(self):
    self.filter_parser = FilterParser()

  def to_sql(self,query,table,acceptable_fields,columns=None,sort_columns=None,field_to_col=None):
    """
    Convert an API query string into a SQL statement.

    This should only be used if:
    * Database privileges for this user are read only
    * The programmer provides the table name, NOT the user
    * The programmer provides the columns to be returned, NOT the user

    Otherwise, you will probably get SQL injected.

    Args:
      query: the filter string as submitted via API request
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

    # def sql_quote(x):
    #   if isinstance(x,str):
    #     return "'{}'".format(x)
    #   else:
    #     return str(x)

    ops = {
      "gt": ">",
      "ge": ">=",
      "le": "<=",
      "lt": "<",
      "eq": "=",
      "not": "<>",
      "in": "IN",
      "=": "=",
      ">": ">",
      "<": "<"
    }

    # If these appear in the SQL string, they need to be quoted.
    sql_keywords = [
      "end"
    ]

    def quote_keywords(x):
      if x in sql_keywords:
        return '"{}"'.format(x)
      else:
        return x

    sql = [
      "SELECT {} FROM {}".format(
        "*" if columns is None else ",".join(map(quote_keywords,columns)),
        table
      )
    ]

    if query is not None:
      matches = self.filter_parser.grammar.parseString(query)
    else:
      matches = []

    params = {}
    pcount = 1

    if len(matches) > 0:
      sql.append("WHERE")

    for match in matches:
      if isinstance(match,str):
        if match == 'and':
          sql.append("AND")
        elif match == 'or':
          sql.append("OR")
      else:
        lhs = field_to_col.get(match.lhs,match.lhs) if field_to_col is not None else match.lhs
        if lhs not in acceptable_fields:
          raise InvalidFieldException, "Invalid field in query string: {}".format(match.lhs)

        sql.append(quote_keywords(lhs))

        sql_comp = ops.get(match.comp)
        if sql_comp is None:
          raise InvalidOperatorException, "Invalid operator in query string: {}".format(match.comp)

        sql.append(ops.get(match.comp))

        if match.comp == "in":
          rhs = list(match.rhs)
        else:
          rhs = list(match.rhs)[0]

        mparam = "p{}".format(pcount)
        if isinstance(rhs,list):
          params[mparam] = tuple(rhs)
          sql.append(":{}".format(mparam))
          #sql.append("({})".format(",".join(map(sql_quote,rhs))))
        else:
          params[mparam] = rhs
          sql.append(":{}".format(mparam))
          #sql.append(str(rhs))

        pcount += 1

    if sort_columns is not None:
      sql.append("ORDER BY {}".format(",".join(map(quote_keywords,sort_columns))))

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
  