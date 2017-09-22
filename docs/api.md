---
title: UM API Reference

language_tabs:
  - shell
  - python

search: true
---

# Introduction

This document contains the specification for the UM data API, used by LocusZoom and other tools under development at the Center for Statistical Genetics, University of Michigan.

# Production or development API

Simply replace `api` with `api_internal_dev` in any of the URLs below.

```shell
# Production API
curl "http://portaldev.sph.umich.edu/api/v1/statistic/single/"

# Development API
curl "http://portaldev.sph.umich.edu/api_internal_dev/v1/statistic/single/"
```

# Common parameters

To retrieve data from available resources, the HTTP GET requests are used with the optional parameters listed in the table below. The list of parameters and their format is based on the best practices from OData and JAX-RS specifications [1],[2].

[1]: http://www.odata.org/documentation/
[2]: http://jax-rs-spec.java.net

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
‘a string’ | Variable length character string.
0.73, -0.73 | Floating point number.
12, -12 | Integer number.

Operator | Description | Example
-------- | ----------- | -------
eq | = | filter=analysis eq 1
| | filter=variant eq ‘rs1234567’
gt | > | filter=refAlleleFreq gt 0.01
lt | < | filter=pvalue lt 0.000000005
ge | >= | filter=position ge 10000
le | <= | filter=position le 20000
in |  | filter=chromosome in ‘1’,’2’,’3’,’16’
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
/statistic/pair/LD/ | Collection of all datasets that have available linkage disequilibrium information or that can be used to compute linkage disequilibrium.
/statistic/pair/LD/results/ | Collection of pair-wise linkage disequilibrium coefficients between all variants.
/statistic/pair/ScoreCov/ | Collection of all datasets that have available covariance matrices between single variant score test statistics.
/statistic/pair/ScoreCov/results/ | Collection of covariance values between all single variant score test statistics.
/annotation/recomb/ | Recombination rates
/annotation/variant/ | Collection of all available single variant annotations.
/annotation/snps/ | List all dbSNP datasets
/annotation/snps/results/ | Query by rsid and find chrom/pos/ref/alt, or vice versa.
/annotation/omnisearch/ | Search for genomic coordinates given a rsID, gene, transcript, etc.
/annotation/intervals/ | Collection of all available genome interval annotation sources (such as GENCODE).
/annotation/intervals/results/ | Collection of all available genome interval annotations.
/annotation/genes/sources/ | Collection of all available gene annotation resources.
/annotation/genes/ | Collection of all annotated genes.
/annotation/genes/names/ | Collection of all gene/transcript/exon names.

# API endpoints

## Single variant statistics

API endpoints for retrieving association statistics on single variants.

### List all available datasets/resources

`GET /statistic/single/`

```shell
curl "http://portaldev.sph.umich.edu/api/v1/statistic/single/"
```

```python
import requests

response = requests.get("http://portaldev.sph.umich.edu/api/v1/statistic/single/")
json = response.json()
```

> The JSON response will look like:

```json
{
  "data": {
    "analysis": [1,2,3],
    "study": ["METSIM","FUSION","FUSION"],
    "trait": ["T2D","T2D","fasting insulin"],
    "tech": ["Illumina300K","Exome chip","Illumina 1M"],
    "build": ["b36","b37","b37"],
    "imputed": ["1000G","NA","HapMap"]
  },
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
analysis | Analysis unique identifier
study | Study name
trait | Trait name
tech | Genotyping/sequencing technology
build | Genome build
imputed | Reference panel used if data was imputed

#### FILTERS

Filter | Description
------ | -----------
analysis in 1,2,... | Selects set of analyses by unique ID

#### SORT

Not yet implemented

### Retrieve results

`GET /statistic/single/results/`

> Example: retrieve all association results in the FUSION study for T2D (analysis ID 1)

```shell
curl -G "http://portaldev.sph.umich.edu/api/v1/statistic/single/results/" --data-urlencode "page=1&limit=100&filter=analysis in '1'"
```

```json
{
  "data": {
    "analysis": [1,1,1],
    "id": ["chr4:1_A/G","chr4:2_C/T","chr4:3900_C/T"],
    "chr": ["4","4","4"],
    "position": [1,2,3900],
    "pvalue": [0.6,0.01,0.000043],
    "scoreTestStat": [0.2,5.4,3.6]
  },
  "lastPage": null
}
```

> Example: Retrieve association results from region 12:10001-20001 from the FUSION study for trait T2D. Include only variant name, position, and p-value columns. Sort by the position and p-value columns.

```shell
curl -G "https://portaldev.sph.umich.edu/api/v1/statistic/single/results/" --data-urlencode "page=1 & limit=100 & filter=analysis in 1 and chromosome in ‘12’ and position ge 10001 and position le 20001 & fields=variant, position, pvalue & sort=position, pvalue"
```

```json
{
  "data": {
    "variant": ["chr12:10001_A/G","chr12:10002_C/T","chr12:20000_G/T"],
    "position": [10001,10002,20000],
    "pvalue": [0.001,0.5,0.03]
  },
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
analysis | Analysis unique identifier
variant | Variant unique name
chromosome | Chromosome
position | Position in base pairs
samples | Number of samples in the model
refAllele | Reference allele
altAllele | Alternate allele
effectAllele | Effect allele
effectAlleleFreq | Effect allele frequency
effectAlleleCount | Effect allele count
refGenotypeCount | Number of homozygous genotypes with reference allele
hetGenotypeCount | Number of heterozygous genotypes
altGenotypeCount | Number of homozygous genotypes with alternate allele
effect | Effect size
effectStdErr | Effect size standard error
scoreStat | Score statistic
pvalue | P-value

#### FILTERS

Filter | Description
------ | -----------
analysis in 1, 2 | Select analysis by a unique identifier
chromosome in ‘1’, ’22’, ’X’ | Select chromosomes by name.
position ge 10000 | Start position in base-pairs of the interval of interest.
position le 60000 | End position in base-pairs of the interval of interest.

#### SORT

Not yet implemented

### PheWAS: all available results for a given variant

`GET /statistic/phewas/`

```shell
# We're using format=objects here as it's probably the preferred way to retrieve the data.
# The standard data frame / array of arrays layout is also available if you remove format=objects.
curl -G "http://portaldev.sph.umich.edu/api_internal_dev/v1/statistic/phewas/?build=GRCh37&format=objects" --data-urlencode "filter=variant eq '10:114758349_C/T'"
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
      "variant": "10:114758349_C/T"
      "chromosome": "10",
      "position": 114758349,
      "build": "GRCh37",
      "ref_allele": "C",
      "ref_allele_freq": null,
      "score_test_stat": null,
      "study": "DIAGRAM",
      "description": "DIAGRAM 1000G T2D meta-analysis",
      "tech": null,
      "pmid": "28566273",
      "trait": "T2D",
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
build | Genome build |
variant | Variant
chromosome | Chromosome for variant
position | Position
log_pvalue | -log10 p-value | Yes
trait | Trait code. Example: "T2D"
trait_label | Longer description of trait, e.g. "Type 2 diabetes" | Yes
trait_group | Arbitrary grouping/category the trait belongs to, e.g. "metabolic diseases" | Yes
description | Description of analysis this dataset represents
study | Study, consortium, or group that generated this analysis
tech | Genotyping/sequencing technology
imputed | Reference panel used if data was imputed

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

### List all datasets/resources

`GET /statistic/pair/LD/`

> Example: list all available reference panels

```shell
curl "http://portaldev.sph.umich.edu/api/v1/statistic/pair/LD/"
```

```json
{
  "data": {
    "reference": [1,2,3,4],
    "panel": ["1000G","1000G","1000G","HapMap"],
    "population": ["JPT", "YRI", "EUR", "JPT"],
    "build": ["b37","b37","b37","b36"],
    "version": ["3","3","3","2"]
  },
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
reference | Reference panel unique identifier
panel | Reference panel name
population | Population name
build | Genome build
version | Reference panel version

#### FILTERS

Filter | Description
------ | -----------
reference in 1, 2 | Select reference by a unique identifier.

#### SORT

Not yet implemented

### Retrieve results

`GET /statistic/pair/LD/results/`

> Example: Retrieve all pair-wise LD D’ values between SNPs in the 12:10001-20001 region using 1000G EUR build 37 version 3 reference panel. Don’t sort the results. Retrieve only variant1, variant2 and value fields. Split results into pages of size 100. Start with the first page.

```shell
curl -G "http://portaldev.sph.umich.edu/api/v1/statistic/pair/LD/results/" --data-urlencode "page=1&limit=100&filter=reference in 3 and chromosome1 in ‘12’ and position1 ge 10001 and position1 le 20001 and chromosome2 in ‘12’ and position2 ge 10001 and position2 le 20001 and type in ‘dprime’ & fields=variant2,variant2,value"
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
curl -G "http://portaldev.sph.umich.edu/api/v1/statistic/pair/LD/results/" --data-urlencode "page=1&limit=100&filter=reference in 3 and variant1 in ’12:10023’ and chromosome2 in ’12’ and position ge 10001 and position le 20001 ant type in ‘dprime’ & fields=variant2,value"
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
variant1 in ’12:1000’, ’12:1001’ | Select first variant by unique name.
chromosome1 in ‘1’, ‘2’ | Select chromosome for the first variant.
position1 ge 1000<br/>position1 le 2000 | Specify positions range (in base-pairs) for the first variant.
variant2 | Select second variant by unique name.
chromosome2 in ‘1’, ‘2’ | Select chromosome for the second variant.
position2 ge 1000<br/>position2 le 2000 | Specify positions range (in base-pairs) for the second variant.
type in ‘dprime’, ‘rsquare’ | Select type of LD coefficient.

#### SORT

Not yet implemented

## Covariance

### List all datasets/resources

`GET /statistic/pair/ScoreCov/`

> Example: Get all available studies that have covariance matrices of score statistics.

```shell
curl "http://portaldev.sph.umich.edu/api/v1/statistic/pair/ScoreCov/"
```

```json
{
  "data": {
    "analysis": [1, 2, 3],
    "study": ["FUSION", "FUSION", "MAGIC"],
    "trait": ["t2d", "t2d", "fasting insulin"],
    "tech": ["Illumina300K", "Exome-chip", "Illumina300K"],
    "build": ["b37", "b37", "b36"],
    "imputed": ["1000G", "NA", "HapMap"]
  },
  "lastPage": null
}
```

> Example: Get available information about the covariance matrix available for the analysis with id equal to 1

```shell
curl -G "http://portaldev.sph.umich.edu/api/v1/statistic/pair/ScoreCov/" --data-urlencode "filter=analysis in 1"
```

```json
{
  "data": {
    "analysis": [1],
    "study": ["FUSION"],
    "trait": ["t2d"],
    "tech": ["Illumina300K"],
    "build": ["b37"],
    "imputed": ["imputed"]
  },
  "lastPage": null
}
```

#### FIELDS

Field | Description
----- | -----------
analysis | Analysis unique name.
study | Study name.
trait | Trait name.
tech | Genotyping/sequencing technology.
build | Genome build version.
imputed | Reference panel used for imputation.

#### FILTERS

Filter | Description
------ | -----------
analysis in 1, 2 | Select analysis that have covariance information available by a unique identifier.

### SORT

Not yet implemented

### Retrieve results

`GET /statistic/pair/ScoreCov/results/`

> Example: Retrieve covariance of score statistics between all SNPs in the 12:10001-20001 region from T2D association results in the FUSION study. Retrieve only variant1, variant2 and value fields. Split results into pages of size 100. Start with the first page.

```
curl -G "http://portaldev.sph.umich.edu/api/v1/statistic/pair/ScoreCov/results/" --data-urlencode "page=1&limit=100&filter=analysis in 1 and chromosome1 in ‘12’ and position1 ge 10001 and position1 le 20001 and chromosome2 in ‘12’ and position2 ge 10001 and position2 le 20001 & fields=variant1,variant2,value"
```

```json
{
  "data": {
    "variant1": ["12:10001", "12:10001", "12:10002"],
    "variant2": ["12:10002", "12:10003", "12:10003"],
    "value": [0.30, 0.43, 0.12]
  },
  "lastPage": 12
}
```

> Example: Retrieve covariance of score statistics between 12:10024 SNP and all SNPs in the 12:10001-20001 region from T2D association results in the FUSION study. Retrieve only variant2 and value fields. Split results into pages of size 100. Start with the first page.

```shell
curl -G "http://portaldev.sph.umich.edu/api_internal_dev/v1/statistic/pair/ScoreCov/results/" --data-urlencode "page=1&limit=100&filter=analysis in 1 and varian1 in ’12:10024’ and chromosome2 in ‘12’ and position2 ge 10001 and position2 le 20001 & fields=variant2,value"
```

```json
{
  "data": {
    "variant2": ["12:10001", "12:10002", "12:10003"],
    "value": [0.55, 0.12, 0.77]
  },
  "lastPage": 10
}
```

> Example: Extract covariance between all markers within the region chr1:762320-862320

```shell
curl -G "http://portaldev.sph.umich.edu/api_internal_dev/v1/pair/ScoreCov/results/" --data-urlencode "filter=analysis in 4 and chromosome1 in '1' and position1 ge 762320 and position1 le 862320 and chromosome2 in '1' and position2 ge 762320 and position2 le 862320"
```

```python
url = "http://portaldev.sph.umich.edu/api_internal_dev/v1/pair/ScoreCov/results/?filter=analysis in 4 and chromosome1 in '1' and position1 ge 762320 and position1 le 862320 and chromosome2 in '1' and position2 ge 762320 and position2 le 862320"

resp = requests.get(url)

data = resp.json()["data"]
```

```json
{
  "data": {
    "variant_name1": ["1:762320_C/T","1:762320_C/T","1:861349_C/T"],
    "chromosome1": ["1","1","1"],
    "position1": [762320,762320,861349],
    "variant_name2": ["1:762320_C/T","1:861349_C/T","1:861349_C/T"],
    "chromosome2": ["1","1","1"],
    "position2": [762320,861349,861349],
    "statistic": [0.00060542,-4.39597E-7,0.00110772]},
  "lastPage":null
}
```

#### FIELDS

Field | Description
----- | -----------
analysis | Analysis unique name.
variant1 | Variant unique name.
chromosome1 | Chromosome name.
position1 | Position in base-pairs.
variant2 | Variant unique name.
chromosome2 | Chromosome name.
position2 | Position in base-pairs.
value | Covariance value.

#### FILTERS

Filter | Description
------ | -----------
analysis in 1, 2 | Select analysis by a unique identifier.
variant1 in ’12:1001’, ’12:1002’ | Select first variant by unique name.
chromosome1 in ‘1’, ‘2’, ‘X’ | Select chromosome for the first variant by name.
position1 ge 1000<br/>position1 le 2000 | Select positions range (in base-pairs) for the first variant.
variant2 in ’12:1001’, ’12:1002’ | Select second variant by unique name.
chromosome2 in ‘1’, ‘2’, ‘X’ | Select chromosome for the second variant by name.
position2 ge 1000<br/>position2 le 2000 | Select positions range (in base-pairs) for the first variant.

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
curl -G "http://portaldev.sph.umich.edu/api_internal_dev/v1/annotation/recomb/results/" --data-urlencode "filter=id in 15 and chromosome eq '21' and position lt 10906989"
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

#### FILTERS

#### SORT

Data can be sorted on any field by adding `&sort=field1,field2` onto your URL.

## Interval annotations

These would be annotations that span intervals of the genome, such as enhancers, TFBSs, etc.

### List all datasets/resources

`GET /annotation/intervals/`

> Example: Retrieve a list of all available interval annotation resources.

```shell
curl "http://portaldev.sph.umich.edu/api_internal_dev/v1/annotation/intervals/"
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
      "b37",
      "b37",
      "b37",
      "b37"
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
curl -G "http://portaldev.sph.umich.edu/api_internal_dev/v1/annotation/intervals/" --data-urlencode "filter=id in 16"
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
curl -G "http://portaldev.sph.umich.edu/api_internal_dev/v1/annotation/intervals/results/" --data-urlencode "filter=id in 16 and chromosome eq '2' and start < 19001"
```

```json
{
  "data": {
    "chromosome": [
      "2",
      "2",
      "2",
      "2",
      "2"
    ],
    "end": [
      11400,
      12000,
      18600,
      19000,
      19200
    ],
    "id": [
      16,
      16,
      16,
      16,
      16
    ],
    "public_id": [
      null,
      null,
      null,
      null,
      null
    ],
    "start": [
      0,
      11400,
      12000,
      18600,
      19000
    ],
    "state_id": [
      13,
      8,
      13,
      8,
      5
    ],
    "state_name": [
      "Heterochromatin / low signal",
      "Insulator",
      "Heterochromatin / low signal",
      "Insulator",
      "Strong enhancer"
    ],
    "strand": [
      null,
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
annotation | An object of key/value pairs of annotations specific to an interval region

#### FILTERS

Filter | Description
------ | -----------
id in 1, 2 | Select interval annotation resource by a unique identifier.
chromosome in ‘1’, ‘2’, ‘X’ | Select chromosome by name.
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
curl "http://portaldev.sph.umich.edu/api/v1/annotation/genes/sources/"
```

```json
{
  "data": [
    {
      "source_id" : 1,
      "source_name" : "gencode",
      "version" : "Release_23",
      "build" : "GRCh38.p3"
    },
    {
      "source_id" : 2,
      "source_name" : "gencode",
      "version" : "Release_22",
      "build" : "GRCh38.p3"
    }
  ]
}
```

#### FIELDS

Field | Description
----- | -----------
source_id | Annotation resource unique id.
source_name | Annotation resource name.
version | Annotation resource version.
build | Annotation resource genome build.

### Retrieve gene information

`GET /annotation/genes/`

> Retrieve all gene annotation data.

```shell
curl "http://portaldev.sph.umich.edu/api/v1/annotation/genes/"
```

```json
{
  "data": [
  {
    "gene_id": "ENSG00000223972.5",
    "gene_name": "DDX11L1",
    "chromosome": "chr1",
    "start": "11869",
    "end": "14409",
    "strand": "+",
    "transcripts": [
    {
      "transcript_id": "ENST00000456328.2",
      "transcript_name": "DDX11L1-002",
      "start": "11869",
      "end": "14409",
      "exons": [
        { "exon_id": "ENSE00002234944.1", "start": " 11869", "end": " 12227" },
        { "exon_id": "ENSE00003582793.1", "start": " 12613", "end": " 12721" },
        { "exon_id": "ENSE00002312635.1", "start": " 13221", "end": " 14409" },
      ]
    },
    {
      "transcript_id": "ENST00000450305.2",
      "transcript_name": "DDX11L1-001",
      "start": "12010",
      "end":"13670",
      "exons": [
        { "exon_id": "ENSE00001948541.1", "start": "12010", "end": "12057" },
        { "exon_id": "ENSE00001671638.2", "start": "12179", "end": "12227" },
        { "exon_id": "ENSE00001758273.2", "start": "12613", "end": "12697" },
        { "exon_id": "ENSE00001799933.2", "start": "12975", "end": "13052" },
        { "exon_id": "ENSE00001746346.2", "start": "13221", "end": "13374" },
        { "exon_id": "ENSE00001863096.1", "start": "13453", "end": "13670" }
      ]
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
source | Genes annotation resource id.
name | Gene name (non-unique).
id | Gene unique id.
chrom | Chromosome name.
region-start | Gene start position.
region-end | Gene end position.
strand | Gene strand

#### FILTERS

Filter | Description
------ | -----------
source in 1, 2 | Selects gene annotation source by a unique identifier.
name in ‘APOE’, ‘TCF7L2’ | Selects gene annotation by non-unique display name(s).
id in ‘ENSG00000223972.5’, ‘ENSG00000227232.5’ | Selects gene annotation by unique gene ID(s).
chrom eq ‘chr20’ | Selects gene annotation that lie within a chromosome.
start ge 20000000 | Selects gene annotation with start positions greater than a certain value.
end le 20100000 | Selects gene annotation with end positions less than a certain value.

#### SORT

Not yet implemented

### Retrieve gene names

`GET /annotation/genes/names/`

> Example: retrieve all searchable regions that begin with the string ‘TCF’.

```shell
curl -G "http://portaldev.sph.umich.edu/api/v1/annotation/genes/names/" --data-urlencode "filter=name startswith ‘TCF’"
```

```json
{
  "data": [
  {
    "region" : "TCF7",
    "label" : "gene_name"
  },
  {
    "region" : "TCF7-001",
    "label" : "transcript_name"
  },
  {
    "region" : "TCF7-002",
    "label" : "transcript_name"
  }
  ]
}
```

#### FIELDS

Field | Description
----- | -----------
region | Gene/transcript/exon name.
label | Type of region: "gene_name", "transcript_name", "exon_name".

#### FILTERS

Filter | Description
------ | -----------
name startswith ‘TCF’, ‘ENSG00001’, ‘ENSG’ | Selects all gene_id, gene_name, transcript_id, transcript_name, and exon_id that start with a string.

#### SORT

Not yet implemented
