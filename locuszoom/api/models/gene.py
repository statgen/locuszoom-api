#!/usr/bin/env python
import json
from copy import deepcopy
from sortedcontainers import SortedSet

class Exon(object):
  cargs = "exon_id chrom start end strand".split()
  def __init__(self,**kwargs):
    for arg in Exon.cargs:
      self.__dict__[arg] = kwargs.get(arg)

  def to_dict(self):
    return deepcopy(self.__dict__)

  def __hash__(self):
    return hash(self.exon_id)

  def __eq__(self,other):
    return self.exon_id == other.exon_id

  def __lt__(self,other):
    if self.chrom == other.chrom:
      if self.start < other.start:
        return True
      else:
        return False
    else:
      raise ValueError("Comparing exons on separate chromosomes")

class Transcript(object):
  cargs = "transcript_id chrom start end strand".split()

  def __init__(self,**kwargs):
    for arg in Transcript.cargs:
      self.__dict__[arg] = kwargs.get(arg)

    self.exons = SortedSet()

  def add_exon(self,exon):
    self.exons.add(exon)

  def to_dict(self):
    dd = {}
    for k in Transcript.cargs:
      v = self.__dict__[k]
      if isinstance(v,(set,SortedSet)):
        v = list(v)

      dd[k] = v

    for e in self.exons:
      dd.setdefault("exons",[]).append(e.to_dict())

    return dd

  def __hash__(self):
    return hash(self.transcript_id)

  def __eq__(self,other):
    return self.transcript_id == other.transcript_id

  def __lt__(self,other):
    if self.chrom == other.chrom:
      if self.start < other.start:
        return True
      else:
        return False
    else:
      raise ValueError("Comparing transcripts on separate chromosomes")

class Gene(object):
  cargs = "gene_id gene_name chrom start end strand".split()

  def __init__(self,**kwargs):
    for arg in Gene.cargs:
      self.__dict__[arg] = kwargs.get(arg)

    self.transcripts = SortedSet()
    self.exons = SortedSet()

  def add_transcript(self,transcript):
    self.transcripts.add(transcript)

  def add_exon(self,exon):
    self.exons.add(exon)

  def to_dict(self):
    """
    Convert this gene object into a dictionary, suitable for returning as JSON.

    Returns:
      dict
    """

    dd = {}
    for k in Gene.cargs:
      v = self.__dict__[k]
      if isinstance(v,(set,SortedSet)):
        v = list(v)

      dd[k] = v

    for t in self.transcripts:
      dd.setdefault("transcripts",[]).append(t.to_dict())

    for e in self.exons:
      dd.setdefault("exons",[]).append(e.to_dict())

    return dd

def test():
  g = Gene(gene_id="ENSG1",gene_name="ABC",chrom="1",start=42,end=800,strand="+")
  t = Transcript(
    transcript_id="ENST1",
    chrom="1",
    start=45,
    end=600,
    strand="+"
  )

  e1 = Exon(
    exon_id="ENSE1",
    chrom="1",
    start=46,
    end=50,
    strand="+"
  )

  e2 = Exon(
    exon_id="ENSE2",
    chrom="1",
    start=52,
    end=58,
    strand="+"
  )

  g.add_transcript(t)
  t.add_exon(e1)
  t.add_exon(e2)
  g.add_exon(e1)
  g.add_exon(e2)

  from pprint import pprint
  pprint(g.to_dict())

  print("Trying to convert to JSON")
  js = json.dumps(g.to_dict())
  pprint(js)
  
