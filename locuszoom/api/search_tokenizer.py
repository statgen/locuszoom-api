import re

class SearchTokenizer:
    def __init__(self, term):
        # remove spaces before/after "operators"
        term = re.sub(r' *([-:+,]) *', r'\1', term)
        # treat remaining spaces as delimiters
        term = re.sub(r'\s+', ';', term)
        # split into tokens
        self.tokens = re.split(r'(\d+|\W+)', term)
        # remove empty tokens
        self.tokens = [x for x in self.tokens if x!= ""]
        self.idx = 0

    def __read_number(self, x):
        hasDecimal = False
        hasSuffix = False
        vals = iter(x)
        num = int(next(vals))
        val = next(vals, None)
        while val is not None:
            if val == ",":
                val = next(vals)
                if len(val) !=3 :
                    raise ValueError
                num = num*1000 + int(val)
            elif val == ".":
                if hasDecimal:
                    raise ValueError
                hasDecimal = True
                val = next(vals)
                num = num + float("0." + val)
            elif val.lower() in ("m", "mb"):
                if hasSuffix:
                    raise ValueError
                hasSuffix = True
                num = num * 1000000
            elif val.lower() in ("k", "kb"):
                if hasSuffix:
                    raise ValueError
                hasSuffix = True
                num = num * 1000
            else:
                raise ValueError
            val = next(vals, None)
        return num

    def __parse_next_term(self, parts, term):
        if ":" in parts:
            sindx = parts.index(":")
            chrom = re.sub("(?i)^chr(om)?","","".join(parts[0:sindx]))
            del parts[0:(sindx+1)] 
            if "-" in parts:
                sindx = parts.index("-")
                start = self.__read_number(parts[0:sindx])
                end = self.__read_number(parts[(sindx+1):])
            elif "+" in parts:
                sindx = parts.index("+")
                pos = self.__read_number(parts[0:sindx])
                offset = self.__read_number(parts[(sindx+1):])
                start = pos - offset
                end = pos + offset
            else:
                start = self.__read_number(parts)
                end = start
            return {"type": "region", "term": term, "chrom": chrom, "start": start, "end": end}
        else:
            if "+" in parts:
                sindx = parts.index("+")
                sterm = "".join(parts[0:sindx])
                offset = self.__read_number(parts[(sindx+1):])
            else:
                sterm = term
                offset = 0
            result = {"type": "other", "term":term, "q": sterm, "offset": offset}
            if re.match(r'(?i)^rs\d+',term):
                result["type"] = "rs"
            elif re.match(r'(?i)^ensg\d+(\.\d+)?', term):
                result["type"] = "egene"
            elif re.match(r'(?i)^enst\d+(\.\d+)?', term):
                result["type"] = "etrans"
            return result

    def get_terms(self):
        while self.idx < len(self.tokens):
            parts = []
            while self.idx < len(self.tokens) and self.tokens[self.idx]!=";":
                parts.append(self.tokens[self.idx])
                self.idx = self.idx + 1
            self.idx = self.idx + 1 # skip delimiter
            term = "".join(parts)
            try:
                term = self.__parse_next_term(parts, term)
            except:
                term = {"term": term, "error": "Unrecognized term"}
            yield term
