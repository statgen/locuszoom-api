---
title: UM API Reference

language_tabs:
  - shell
  - python

search: true
---

# Introduction

This document contains the specification for the UM data API, used by LocusZoom and other tools under development at the Center for Statistical Genetics, University of Michigan.

Our API naturally evolves over time as key data is revised. Most annotations (genes, recombination, LD) now support 
both build GRCh37 and build GRCh38. We encourage you to explore the provided metadata endpoints to find the newest and best 
annotations that match your data.

# Production or development API

Simply replace `api` with `api_internal_dev` in any of the URLs below.

```shell
# Production API
curl "https://portaldev.sph.umich.edu/api/v1/statistic/single/"

# Development API
curl "https://portaldev.sph.umich.edu/api_internal_dev/v1/statistic/single/"
```

# Common parameters

To retrieve data from available resources, the HTTP GET requests are used with the optional parameters listed in the table below. The list of parameters and their format is based on the best practices from OData and JAX-RS specifications [1],[2].

[1]: https://www.odata.org/documentation/
[2]: https://jax-rs-spec.java.net

Parameter | Type | Description
--------- | ---- | -----------
page | integer | Page number if pagination is requested
limit | integer | Maximum page size
filter | string | Specifies filtering options
sort | string | List of fields that will be used to sort the collection
fields | string | List of fields that will be included

## filter

The filter parameter allows elimination of redundant resource’s entries using logical expressions. The logical expression is the combination of resource field names, operators and literals. The tables below list available literals and operators correspondingly.

Literal | Description
------- | -----------
'a string' | Variable length character string.
0.73, -0.73 | Floating point number.
12, -12 | Integer number.

Operator | Description | Example
-------- | ----------- | -------
eq | = | filter=analysis eq 1
| | filter=variant eq 'rs1234567'
gt | > | filter=refAlleleFreq gt 0.01
lt | < | filter=pvalue lt 0.000000005
ge | >= | filter=position ge 10000
le | <= | filter=position le 20000
in | | filter=chromosome in '1','2','3','16'
and | & | filter=position ge 10000 and position le 20000

Depending on the requirements, only part of the operators may be supported for a particular resource and its field.

## fields

The fields parameter allows projection of resource’s fields. The projection is specified as a comma separated list of resource’s fields. For example, to select only analysis and trait fields from the /statistic/single resource, the corresponding GET request must have fields=analysis,trait.

Each request has its own set of fields (specified under the API endpoints section.)

## sort

The sort parameter allows ordering of the results based on one or multiple resource’s fields. The fields are provided in a comma separated list. The `-` character before the field name corresponds to the descending order.

# Response status codes

Code | Message | Description
---- | ------- | -----------
200 | JSON with results | Success
400 | Incorrect syntax in filter parameter | Server unable to parse filter
400 | Incorrect syntax in fields parameter | Serve unable to parse the fields parameter
501 | Unsupported data type for the `xyz` field in the filter parameter | Server successfully parsed the filter parameter, but the `xyz` field's data type didn't match the provided literal's type
501 | Unsupported operation for the <xyz> field in the filter parameter | Server successfully parsed the filter parameter, but the resource doesn’t support the specified operation with the <xyz> field
501 | Unsupported field in the filter parameter | Server successfully parsed the filter parameter, but at least one of the specified field names is not present in the corresponding resource
501 | Unsupported field in the fields parameter | Server successfully parsed the filter parameter, but at least one of the specified field names is not present in the corresponding resource

# Response JSON

All responses from HTTP GET requests are represented using JSON data format. The returned object must have two mandatory "data" and "lastPage" fields.

> Example JSON response:

```json
{
  "data": "result JSON here",
  "lastPage": "integer here"
}
```

# Overview of API endpoints

Relative Resource URI | Description
--------------------- | -----------
/statistic/single/ | Collection of all available studies that have single variant association results.
/statistic/single/results/ | Collection of all single variant association results.
/statistic/phewas/ | Return all available association statistics given a variant.
/statistic/pair/LD/results/ | Collection of pair-wise linkage disequilibrium coefficients between all variants.
/annotation/recomb/ | Recombination rates
/annotation/variant/ | Collection of all available single variant annotations.
/annotation/snps/ | List all dbSNP datasets
/annotation/snps/results/ | Query by rsid and find chrom/pos/ref/alt, or vice versa.
/annotation/omnisearch/ | Search for genomic coordinates given a rsID, gene, transcript, etc.
/annotation/intervals/ | Collection of all available genome interval annotation sources (such as GENCODE).
/annotation/intervals/results/ | Collection of all available genome interval annotations.
/annotation/genes/sources/ | Collection of all available gene annotation resources.
/annotation/genes/ | Collection of all annotated genes.
/annotation/gwascatalog/ | Collection of GWAS catalogs
/annotation/gwascatalog/results/ | Collection of GWAS catalogs

# API endpoints

## Single variant statistics

API endpoints for retrieving association statistics on single variants.

### List all available datasets/resources

`GET /statistic/single/`

```shell
curl "https://portaldev.sph.umich.edu/api/v1/statistic/single/"
```

```python
import requests

response = requests.get("https://portaldev.sph.umich.edu/api/v1/statistic/single/")
json = response.json()
```

> The JSON response will look like:

```json
{
  "data": {
    "analysis": [1, 2, 3],
    "build": ["GRCh37", "GRCh37", "GRCh37"],
    "date": ["2010-01-17", "2010-01-17", "2010-01-17"],
    "first_author": ["Fritsche LG", "Welch R", "Willer CJ"],
    "last_author": ["Willer CJ", "Abecasis GR", "Mohlke JL"],
    "study": ["METSIM", "FUSION", "FUSION"],
    "trait": ["T2D", "T2D", "fasting insulin"],
    "tech": ["Illumina300K", "Exome chip", "Illumina 1M"],
    "imputed": ["1000G", "NA", "HapMap"]
  },
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
id | Analysis unique identifier
analysis | Human-readable analysis label
study | Study name
trait | Trait name
tech | Genotyping/sequencing technology
build | Genome build
imputed | Reference panel used if data was imputed

#### FILTERS

Filter | Description
------ | -----------
id in 1,2,... | Selects set of analyses by unique ID

#### SORT

Not yet implemented

### Retrieve results

`GET /statistic/single/results/`

> Example: retrieve all association results in the FUSION study for T2D (analysis ID 1)

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/statistic/single/results/" --data-urlencode "page=1" --data-urlencode "limit=100" --data-urlencode "filter=analysis in '99'"
```

```json
{
  "data": {
    "analysis": [1, 1, 1],
    "beta": [null, null, null],
    "chromosome": ["4", "4", "4"],
    "log_pvalue": [0.22, 2, 4.37],
    "position": [1, 2, 3900],
    "ref_allele": ["A", "C", "C"],
    "ref_allele_freq": [null, null, null],
    "score_test_stat": [0.2, 5.4, 3.6],
    "se": [null, null, null],
    "variant": ["4:1_A/G", "4:2_C/T", "4:3900_C/T"]
  },
  "lastPage": null
}
```

> Example: Retrieve association results from region 12:10001-20001 from the FUSION study for trait T2D. Include only variant name, position, and p-value columns. Sort by the position and p-value columns.

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/statistic/single/results/" --data-urlencode "page=1" --data-urlencode "limit=100" --data-urlencode "filter=analysis in 1 and chromosome in '12' and position ge 10001 and position le 20001" --data-urlencode "fields=variant, position, log_pvalue"  --data-urlencode "sort=log_pvalue"
```

```json
{
  "data": {
    "variant": ["12:10001_A/G", "12:10002_C/T", "12:20000_G/T"],
    "position": [10001, 10002, 20000],
    "log_pvalue": [0.001, 0.03, 0.5]
  },
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
analysis | Analysis unique identifier
beta | Effect size
chromosome | Chromosome
log_pvalue | -log10 p-value
position | Position in base pairs
ref_allele | Reference allele
ref_allele_freq | Reference allele frequency
score_test_stat | Score statistic
se | Effect size standard error
variant | Variant unique name (A string in the scheme {chrom}:{pos}_{ref}/{alt})

#### FILTERS

Filter | Description
------ | -----------
analysis in 1, 2 | Select analysis by a unique identifier
chromosome in '1', '22', 'X' | Select chromosomes by name.
position ge 10000 | Start position in base-pairs of the interval of interest.
position le 60000 | End position in base-pairs of the interval of interest.

#### SORT

Add `&sort=field1,field2` to your URL. If the field is not present it will have no effect.

### PheWAS: all available results for a given variant

`GET /statistic/phewas/`

```shell
# We're using format=objects here as it's probably the preferred way to retrieve the data.
# The standard data frame / array of arrays layout is also available if you remove format=objects.
curl -G "https://portaldev.sph.umich.edu/api/v1/statistic/phewas/?build=GRCh37&format=objects" --data-urlencode "filter=variant eq '10:114758349_C/T'"
```

> The JSON response will look like:

```json
{
  "data": [
    {
      "id": 45,
      "trait_group": "Metabolic disease",
      "trait_label": "Type 2 diabetes",
      "log_pvalue": 107.032,
      "variant": "10:114758349_C/T",
      "chromosome": "10",
      "position": 114758349,
      "build": "GRCh37",
      "beta": null,
      "ref_allele": "C",
      "ref_allele_freq": null,
      "score_test_stat": null,
      "se": null,
      "study": "DIAGRAM",
      "description": "DIAGRAM 1000G T2D meta-analysis",
      "tech": null,
      "pmid": "28566273",
      "trait": "T2D"
    }
  ],
  "lastPage": null,
  "meta": {
    "build": [
      "GRCh37"
    ]
  }
}
```

#### FIELDS

Field | Description | Must exist in response for PheWAS module
----- | ----------- | ----------------------------------------
id | Unique identifier for each dataset | Yes
beta | Effect size |
build | Genome build |
chromosome | Chromosome for variant
description | Description of analysis this dataset represents
log_pvalue | -log10 p-value | Yes
pmid | pmid | PubMed ID for paper if this dataset is published | 
position | Position
study | Study, consortium, or group that generated this analysis
tech | Genotyping/sequencing technology
ref_allele | Reference allele
ref_allele_freq | Reference allele frequency
score_test_stat | Score statistic
se | Effect size standard error
study | Study name |
trait | Trait code. Example: "T2D"
trait_label | Longer description of trait, e.g. "Type 2 diabetes" | Yes
trait_group | Arbitrary grouping/category the trait belongs to, e.g. "metabolic diseases" | Yes
variant | Variant unique name (A string in the scheme {chrom}:{pos}_{ref}/{alt})

#### PARAMETERS

Param | Description
----- | -----------
build | Genome build for the requested variant. For example 'GRCh37' or 'GRCh38'. Trailing version (e.g. p13.3) will not be present.
format | Format of the response. Our API server supports two formats - the default is an array of arrays, and the optional `objects` format returns an array of JSON objects. LocusZoom.js will only generate requests that use `format=objects`. 

#### FILTERS

Filter | Description
------ | -----------
variant eq 'X' | Select results for this variant. Variant should be in `chr:pos_ref/alt` format.

#### META

Response will contain a `meta` object, with the following attributes:

Attribute | Value
--------- | -----
build | Array of genome build(s) that were requested. Records returned will be only for these builds. This will typically only be 1 build. In the future we may begin upconverting variants to other builds. 

#### SORT

Not yet implemented

## Linkage disequilibrium
The PortalDev API endpoint has been deprecated. We encourage you to explore the new Michigan LDServer. The interactive 
"[LD playground](https://portaldev.sph.umich.edu/playground)" tool provides a concise overview of possible options. For
 many practical applications (such as LocusZoom plots), the "variant correlations" feature is recommended. 

### Retrieve results

**Although the endpoint documented below still exists, it is deprecated and may be removed in the future. The 
documentation for this old endpoint is not maintained and is not guaranteed to be accurate.**

`GET /statistic/pair/LD/results/`

> Example: Retrieve all pair-wise LD D’ values between SNPs in the 12:10001-20001 region using 1000G EUR build 37 version 3 reference panel. Don’t sort the results. Retrieve only variant1, variant2 and value fields. Split results into pages of size 100. Start with the first page.

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/statistic/pair/LD/results/" --data-urlencode "page=1" --data-urlencode "limit=100" --data-urlencode "filter=reference in 1 and chromosome1 in '12' and position1 ge 10001 and position1 le 20001 and chromosome2 in '12' and position2 ge 10001 and position2 le 20001 and type in 'dprime'" --data-urlencode "fields=variant2,variant2,value"
```

```json
{
  "data": {
    "variant1": ["12:10001", "12:10001", "12:10002"],
    "variant2": ["12:10002", "12:10003", "12:10003"],
    "value": [1.00, 0.78, 1.00]
  },
  "lastPage": 12
}
```

> Example: Retrieve pair-wise D’ LD values between SNP 12:10023 and all SNPs in the 12:10001-20001 region using 1000G EUR build 37 version 3 reference panel. Retrieve only variant2 and value columns. Split the results into pages of size 100. Start with the first page.

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/statistic/pair/LD/results/" --data-urlencode "page=1&limit=100&filter=reference in 3 and variant1 in '12:10023' and chromosome2 in '12' and position ge 10001 and position le 20001 and type in 'dprime'&fields=variant2,value"
```

```json
{
  "data": {
    "id2": ["12:10001", "12:10002", "12:10003"],
    "value": [1.00, 1.00, 0.98]
  },
  "lastPage": 10
}
```

This API endpoint calculates LD values between pairs of variants on the fly (not precomputed). For regions of 1 MB, it should be nearly instant.

This endpoint only uses pre-existing reference panels, such as the 1000 Genomes panels.

#### FIELDS

Field | Description
----- | -----------
reference | Reference panel unique identifier
variant1 | Variant name in chr:pos_ref/alt format
chromosome1 | Chromosome
position1 | Position in base pairs
variant2 |
chromosome2 |
position2 |
value | LD value
type | LD type: dprime, rsquare

#### FILTERS

Filter | Description
------ | -----------
reference in 1, 2 | Select reference by unique identifier.
variant1 in '12:1000', '12:1001' | Select first variant by unique name.
chromosome1 in '1', '2' | Select chromosome for the first variant.
position1 ge 1000<br/>position1 le 2000 | Specify positions range (in base-pairs) for the first variant.
variant2 | Select second variant by unique name.
chromosome2 in '1', '2' | Select chromosome for the second variant.
position2 ge 1000<br/>position2 le 2000 | Specify positions range (in base-pairs) for the second variant.
type in 'dprime', 'rsquare' | Select type of LD coefficient.

#### SORT

Not yet implemented

## Recombination

### Get recombination sources

`GET /annotation/recomb/`

#### FIELDS

Field | Description
----- | -----------
id | Recombination rate map unique identifier
name | Recombination rate map (e.g. hapmap)
build | Genome build for recombination rate positions
version | Version string for this recombination map (usually a date)

#### FILTERS

Filter | Description
------ | -----------
id in 1 | Select recombination rate by identifier

#### SORT

Add `&sort=field1,field2` to your URL.

### Retrieve recombination rates

`GET /annotation/recomb/results/`

> Example: Retrieve recombination rates within a specific interval for a given dataset

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/annotation/recomb/results/" --data-urlencode "filter=id in 15 and chromosome eq '21' and position gt 10406989 and position lt 10906989"
```

```json
{
  "data": {
    "chromosome": [
      "21",
      "21",
      "21"
    ],
    "id": [
      15,
      15,
      15
    ],
    "pos_cm": [
      0.0,
      0.052685,
      0.052781
    ],
    "position": [
      10865933,
      10906723,
      10906915
    ],
    "recomb_rate": [
      1.29162,
      0.496586,
      0.424224
    ]
  },
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
id | Recombination rate map unique identifier
chromosome | Chromosome
position | Genomic position (bp)
pos_cm | Genetic position (cM)
recomb_rate | Recombination rate

If no ID is specified in the filter string, the best recommended recombination rate source will be chosen. This is currently HapMap Phase 2. The `build` parameter must also be specified.  

#### FILTERS

#### PARAMETERS

Param | Description
----- | -----------
build | Explicitly set the genome build for this endpoint. This affects how the recommended recombination rate source is selected when no ID is present in the filter string.

#### SORT

Data can be sorted on any field by adding `&sort=field1,field2` onto your URL.

## Search endpoints

### Omnisearch

Search for genomic coordinates given a rsID, gene, transcript, etc. The following example search formats are supported:

* chr:position
* chr:start-stop
* chr:position+offset (-> chr:position-offset - chr:position+offset)
* rs00001
* rs00001+offset
* gene symbol names
* transcript names 

Positions and offsets may have commas and use K and M suffixes.

`GET /annotation/omnisearch/`

> Example: Find gene positions by gene name

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/annotation/omnisearch/"  --data-urlencode "q=TCF7L2" --data-urlencode "build=GRCh37"
```

```json
{
  "build": "grch37", 
  "data": [
    {
      "chrom": "10", 
      "end": 114927437, 
      "gene_id": "ENSG00000148737.11", 
      "gene_name": "TCF7L2", 
      "start": 114710009, 
      "term": "TCF7L2", 
      "type": "other"
    }
  ]
}
```

#### FIELDS

Field | Description
----- | -----------
chrom | The chromosome
start | The start genomic position
end | The end genomic position
term | The term used as the query
type | The type of query (egene, region, rs, other), as predicted by the parser

Additional fields may be returned depending on the query type.

#### QUERY PARAMS

Param | Description
----- | -----------
q | A string value to search for
build | A genome build identifier (GRCh37, GRCh38)

## Interval annotations

These would be annotations that span intervals of the genome, such as enhancers, TFBSs, etc.

### List all datasets/resources

`GET /annotation/intervals/`

> Example: Retrieve a list of all available interval annotation resources.

```shell
curl "https://portaldev.sph.umich.edu/api/v1/annotation/intervals/"
```

```json
{
  "data": {
    "assay": [
      "ChIP-seq",
      "ChIP-seq",
      "ChIP-seq",
      "ChIP-seq"
    ],
    "build": [
      "GRCh37",
      "GRCh37",
      "GRCh37",
      "GRCh37"
    ],
    "cell_line": [
      null,
      null,
      "GM12878",
      "K562"
    ],
    "description": [
      "Pancreatic islet chromHMM calls from Parker 2013",
      "Pancreatic islet stretch enhancers from Parker 2013",
      "Chromatin State Segmentation by HMM from ENCODE/Broad",
      "Chromatin State Segmentation by HMM from ENCODE/Broad"
    ],
    "histone": [
      null,
      null,
      null,
      null
    ],
    "id": [
      16,
      17,
      18,
      19
    ],
    "pmid": [
      "24127591",
      "24127591",
      "21441907",
      "21441907"
    ],
    "protein": [
      null,
      null,
      null,
      null
    ],
    "study": [
      "Parker 2013",
      "Parker 2013",
      "ENCODE",
      "ENCODE"
    ],
    "tissue": [
      "pancreatic_islet",
      "pancreatic_islet",
      null,
      null
    ],
    "type": [
      "chromHMM",
      "stretch_enhancers",
      "chromHMM",
      "chromHMM"
    ],
    "url": [
      "http://research.nhgri.nih.gov/manuscripts/Collins/islet_chromatin/",
      "http://research.nhgri.nih.gov/manuscripts/Collins/islet_chromatin/",
      "http://genome.ucsc.edu/cgi-bin/hgFileUi?db=hg19&g=wgEncodeBroadHmm",
      "http://genome.ucsc.edu/cgi-bin/hgFileUi?db=hg19&g=wgEncodeBroadHmm"
    ],
    "version": [
      "2013-12-10",
      "2013-12-10",
      "2012-04",
      "2012-04"
    ]
  },
  "lastPage": null
}
```

> Example: Retrieve information about the interval annotation resource with id equal to 16.

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/annotation/intervals/" --data-urlencode "filter=id in 16"
```

```json
{
  "data": {
    "assay": [
      "ChIP-seq"
    ],
    "build": [
      "b37"
    ],
    "cell_line": [
      null
    ],
    "description": [
      "Pancreatic islet chromHMM calls from Parker 2013"
    ],
    "histone": [
      null
    ],
    "id": [
      16
    ],
    "pmid": [
      "24127591"
    ],
    "protein": [
      null
    ],
    "study": [
      "Parker 2013"
    ],
    "tissue": [
      "pancreatic_islet"
    ],
    "type": [
      "chromHMM"
    ],
    "url": [
      "http://research.nhgri.nih.gov/manuscripts/Collins/islet_chromatin/"
    ],
    "version": [
      "2013-12-10"
    ]
  },
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
id | Unique identifier for interval dataset
study | Name of study (ENCODE, FUSION, etc.)
build | Genome build to which these intervals are anchored
type | Dataset type (chromHMM calls, stretch enhancers, etc.)
version | Version string, usually a date
description | Long description of dataset
assay | Assay used to generate intervals (ChIP-seq, ATAC-seq, etc.)
cell_line | Name of cell line in which these genomic intervals were discovered in
tissue | Name of tissue in which these genomic intervals were discovered in
histone | If the dataset was ChIP-seq for a particular histone, this will be the name of the histone mark
protein | If the dataset was ChIP-seq for a particular TF/DNA-binding protein, this will be the protein (ENSEMBL ID)
pmid | PubMed ID for paper if this dataset is published
url | URL that contains information about the dataset and/or the original downloaded files

#### FILTERS

Filter | Description
------ | -----------
id in 1, 2 | Selects interval annotation resource by a unique identifier.

#### SORT

Sort on any field using `sort=field1,field2`.

### Retrieve interval annotations

`GET /annotation/intervals/results/`

> Retrieve annotations from dataset with id 16, on chromosome 2, with start positions < 19001

```shell
curl -G https://portaldev.sph.umich.edu/api/v1/annotation/intervals/results/ --data-urlencode "filter=id in 19 and chromosome eq '10' and start le 115067678 and end ge 114550452"
```

```json
{
  "data": {
    "chromosome": ["10", "10", "10", "10"],
    "end": [114574010, 114574210, 114575010, 114575210],
    "id": [19, 19, 19, 19],
    "public_id": [null, null, null, null],
    "start": [114516210, 114574010, 114574210, 114575010],
    "state_id": [13, 7, 13, 7],
    "state_name": [
      "Heterochromatin / low signal",
      "Insulator",
      "Heterochromatin / low signal",
      "Insulator"
    ],
    "strand": [
      null,
      null,
      null,
      null
    ]
  },
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
id | Interval dataset identifier
state_id | A (numeric) state identifier for this annotation, such as determined by ChromHMM. (if applicable)
state_name | A human-readable state name that generally corresponds to an entry in state_id. (if applicable)
public_id | Public/other database ID for this interval (if applicable)
chromosome | Chromosome
start | Start of interval (in bp)
end | End of interval (in bp)
strand | DNA strand that the interval is annotated to (if applicable)

#### FILTERS

Filter | Description
------ | -----------
id in 1, 2 | Select interval annotation resource by a unique identifier.
chromosome in '1', '2', 'X' | Select chromosome by name.
start ge 10000<br/>start le 20000 | Select interval if its start position falls into the specified interval.
end ge 10000<br/>end le 20000 | Select interval if its end position falls into the specified interval.

#### SORT

Sort on any field by adding `sort=field1,field2` to the URL.

#### FORMATS

The default format returns JSON where each key is a column name, and the value is an array of values (one per row entry.)

An alternative format returns each row as an object itself. Add `format=objects` to the URL for this.

## Genes

### List all possible sources of gene annotations

Currently we only include ENSEMBL/GENCODE.

`GET /annotation/genes/sources/`

> Example: retrieve all gene annotation sources

```shell
curl "https://portaldev.sph.umich.edu/api/v1/annotation/genes/sources/?format=objects"
```

```json
{
  "data": [
    {
      "genome_build": "GRCh38", 
      "id": 1, 
      "organism": "human", 
      "source": "gencode", 
      "taxid": 9606, 
      "version": "27"
    }, 
    {
      "genome_build": "GRCh37", 
      "id": 2, 
      "organism": "human", 
      "source": "gencode", 
      "taxid": 9606, 
      "version": "19"
    }, 
    {
      "genome_build": "GRCh37", 
      "id": 3, 
      "organism": "human", 
      "source": "gencode", 
      "taxid": 9606, 
      "version": "27"
    }
  ],
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
id | Annotation resource unique id.
genome_build | Annotation resource genome build.
organism |
source | Annotation resource name.
taxid |
version | Annotation resource version.

### Retrieve gene information

`GET /annotation/genes/`

> Retrieve all gene annotation data.

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/annotation/genes/" --data-urlencode "filter=source in 3 and chrom eq '10' and start le 115067678 and end ge 114550452"
```

```json
{
  "data": [
    {
      "chrom": "10", 
      "end": 114578503, 
      "exons": [
        {
          "chrom": "10", 
          "end": 114207225, 
          "exon_id": "ENSE00001449955.2_1", 
          "start": 114206756, 
          "strand": "+"
        }, 
        {
          "chrom": "10", 
          "end": 114207225, 
          "exon_id": "ENSE00001882813.1_1", 
          "start": 114206757, 
          "strand": "+"
        }
      ], 
      "gene_id": "ENSG00000151532.13_2", 
      "gene_name": "VTI1A", 
      "start": 114206756, 
      "strand": "+", 
      "transcripts": [
        {
          "chrom": "10", 
          "end": 114210484, 
          "exons": [
            {
              "chrom": "10", 
              "end": 114207225, 
              "exon_id": "ENSE00001449955.2_1", 
              "start": 114206756, 
              "strand": "+"
            }
          ], 
          "start": 114206992, 
          "strand": "+", 
          "transcript_id": "ENST00000489142.5_1"
        }
      ]
    }
  ], 
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
source | Genes annotation resource id (used for queries)
gene_name | Gene name (non-unique).
gene_id | Gene unique id.
chrom | Chromosome name.
start | Gene start position.
end | Gene end position.
strand | Gene strand
transcripts | A nested object defining available transcripts, and each exon within each transcript

If no source is specified in the filter string, the best recommended gene source will be chosen. This is currently the latest version of GENCODE. The `build` parameter must also be specified.

#### FILTERS

Filter | Description
------ | -----------
source in 1, 2 | Selects gene annotation source by a unique identifier.
gene_name in 'APOE', 'TCF7L2' | Selects gene annotation by non-unique display name(s).
gene_id in 'ENSG00000223972.5', 'ENSG00000227232.5' | Selects gene annotation by unique gene ID(s).
chrom eq 'chr20' | Selects gene annotation that lie within a chromosome.
start ge 20000000 | Selects gene annotation with start positions greater than a certain value.
end le 20100000 | Selects gene annotation with end positions less than a certain value.

#### PARAMETERS

Param | Description
----- | -----------
build | Explicitly set the genome build for this endpoint. This affects how the recommended gene source is selected when no ID is present in the filter string.

#### SORT

Not yet implemented

## GWAS Catalogs

### List all available GWAS catalogs

We currently support the EBI GWAS catalog, and the UK BioBank GWAS hits.

`GET /annotation/gwascatalog/`

> Example: retrieve all GWAS catalogs

```shell
curl "https://portaldev.sph.umich.edu/api/v1/annotation/gwascatalog/"
```

```json
{
  "data": {
    "catalog_version": [
      "e91_r2018-03-13",
      "e91_r2018-03-13"
    ],
    "date_inserted": [
      "2018-03-18T17:20:40-04:00",
      "2018-03-18T17:20:40-04:00"
    ],
    "genome_build": [
      "GRCh38",
      "GRCh37"
    ],
    "id": [
      1,
      2
    ],
    "name": [
      "EBI GWAS Catalog",
      "EBI GWAS Catalog"
    ]
  },
  "lastPage": null
}
```

> Or alternatively in object mode:

```shell
curl "https://portaldev.sph.umich.edu/api/v1/annotation/gwascatalog/?format=objects"
```

```json
{
  "data": [
    {
      "catalog_version": "e91_r2018-03-13",
      "date_inserted": "2018-03-18T17:20:40-04:00",
      "genome_build": "GRCh38",
      "id": 1,
      "name": "EBI GWAS Catalog"
    },
    {
      "catalog_version": "e91_r2018-03-13",
      "date_inserted": "2018-03-18T17:20:40-04:00",
      "genome_build": "GRCh37",
      "id": 2,
      "name": "EBI GWAS Catalog"
    }
  ],
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
id | Unique ID assigned to each GWAS catalog
name | Name of the catalog, e.g. "EBI" or "UKBB"
genome_build | Positions in the catalog are anchored to this build
catalog_version | Version of the GWAS catalog (varies by catalog)
date_inserted | Date the GWAS catalog was inserted into the database

### Retrieve variants from one or multiple GWAS catalogs

`GET /annotation/gwascatalog/results/`

> Retrieve all known disease/trait associated variants within a genomic region for a specific catalog

Understanding the format is easier in object mode, so we use that below.

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/annotation/gwascatalog/results/?format=objects" --data-urlencode "filter=id eq 1 and chrom eq '10' and pos le 112998595 and pos ge 112998585"
```

```json
{
  "data": [
    {
      "alt": "T",
      "chrom": "10",
      "first_author": "Sladek R",
      "genes": "TCF7L2",
      "id": 1,
      "log_pvalue": 33.7,
      "or_beta": 1.65,
      "pmid": "17293876",
      "pos": 112998590,
      "pubdate": "2007-02-11",
      "ref": "C",
      "risk_allele": "T",
      "risk_frq": 0.3,
      "rsid": "rs7903146",
      "study": "A genome-wide association study identifies novel risk loci for type 2 diabetes.",
      "trait": "Type 2 diabetes",
      "trait_group": "Type 2 diabetes",
      "variant": "10:112998590_C/T"
    },
    {
      ...
    }
  ]
}
```

One record is returned per variant * trait * pmid. The same variant <--> trait association can be reported in multiple publications.

> Retrieve associations for a specific variant

> You should use a catalog that is anchored to the same genome build as your variant (since it contains a position.)
> For example, `10:112998590_C/T` is rs7903146 in GRCh38, but `10:114758349_C/T` in GRCh37.
> In this example, assume the GWAS catalog with ID 1 is a GRCh38 catalog.

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/annotation/gwascatalog/results/?format=objects" --data-urlencode "filter=id eq 1 and variant eq '10:112998590_C/T'"
```

> You can also retrieve by rsID instead of a variant:

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/annotation/gwascatalog/results/?format=objects" --data-urlencode "filter=id eq 1 and rsid eq 'rs7903146'"
```

#### FIELDS

Field | Description
----- | -----------
id | GWAS catalog ID
alt | Alternate allele
chrom | Chromosome
first_author | First author of the publication reporting this association
log_pvalue | -log10 p-value for association between variant and trait
or_beta | Effect size (or odds ratio if binary trait)
pmid | PubMed ID for the publication reporting this association
pos | Position
pubdate | Publication date (YYYY-MM-DD)
ref | Reference allele
risk_allele | Specifies allele for effect direction and risk frequency
risk_frq | Frequency of risk allele
rsid | rsID of the variant
study | A human-readable description of the study
trait | Name of the trait/phenotype/disease
trait_group | Grouping of traits as defined by the catalog
variant | Variant in chr:pos_ref/alt format

If no ID is specified in the filter string, the best recommended GWAS catalog will be chosen. This is currently the latest version of the EBI GWAS catalog. The `build` parameter must also be specified.

#### FILTERS

Filter | Description
------ | -----------
id in 1, 3, 6 | Selects GWAS catalogs by their IDs
chrom eq '6' | Select only variants on a particular chromosome
pos ge 1 | Select only variants with position greater than or equal to a value
pos le 10 | Select only variants with position less than or equal to a value
pos gt 1 | Select only variants with position greater than a value
pos lt 10 | Select only variants with position less than a value
variant eq '10:112998590_C/T' | Select a particular variant
rsid eq 'rs7903146' | Select a variant by rsID

#### PARAMETERS

Param | Description
----- | -----------
variant_format | Default variant format is EPACTS style, e.g. 'chr:pos_ref/alt'. Specify variant_format='colons' to get variants of the form 'chr:pos:ref:alt'.
decompose | Decompose multiallelic variants into separate entries, one per every combination of REF/ALT alleles. This is a boolean parameter and can be turned on with any value, e.g. decompose=1 or decompose=true.
build | Explicitly set the genome build for this endpoint. This affects how the recommended gene source is selected when no ID is present in the filter string.

#### SORT

Return sorted results by including the `sort=field` parameter. Probably the most common would be to sort by log p-value, for example `sort=log_pvalue`.

