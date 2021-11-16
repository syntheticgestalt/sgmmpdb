"Implement the 'help' commands"

# mmpdb - matched molecular pair database generation and analysis
#
# Copyright (c) 2015-2017, F. Hoffmann-La Roche Ltd.
# Copyright (c) 2021, Andrew Dalke Scientific, AB
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#    * Neither the name of F. Hoffmann-La Roche Ltd. nor the names of
#      its contributors may be used to endorse or promote products
#      derived from this software without specific prior written
#      permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#


import click

from .click_utils import command

import shutil

def wrap(text):
    width = shutil.get_terminal_size()[0]
    if width < 10:
        width = 10
    else:
        width = width - 2

    text = text.strip("\r\n")
        
    text = click.wrap_text(text, width=width, preserve_paragraphs=True)
    click.echo(text)

#### mmpdb help

@command(name="help")
def help_():
    "summarize the help commands"
    from . import epilog
    wrap(epilog)


#### mmpdb help-analysis

@command(name="help-analysis")
def help_analysis():
    "overview on how to use mmpdb for structure analysis"
    wrap("""
The overall process is:

  1) Fragment structures in a SMILES file, to produce fragments.

  2) Index the fragments to produces matched molecular pairs.
     (you might include property information at this point)

  3) Load property information.

  4) Find transforms for a given structure; and/or

  5) Predict a property for a structure given the known
     property for another structure

Some terminology:

A fragmentation cuts 1, 2, or 3 non-ring bonds to
convert a structure into a "constant" part and a "variable" part. The
substructure in the variable part is a single fragment, and often
considered the R-groups, while the constant part contains one
fragment for each cut, and it often considered as containing the
core.

The matched molecular pair indexing process finds all pairs which have
the same constant part, in order to define a transformation from one
variable part to another variable part. A "rule" stores information
about a transformation, including a list of all the pairs for that
rule.

The "rule environment" extends the transformation to include
information about the local environment of the attachment points on
the constant part. The environment fingerprint is based on the RDKit
circular fingerprints for the attachment points. There is one rule
environment for each available radius. Larger radii correspond to more
specific environments. The "rule environment statistics" table stores
information about the distribution of property changes for all of the
pairs which contain the given rule and environment, with one table
for each property.

#### 1) Fragment structures

Use "`smifrag`" to see how a given SMILES is fragmented. Use "`fragment`"
to fragment all of the compounds in a SMILES file.

"`mmpdb smifrag`" is a diagnostic tool to help understand how a given
SMILES will be fragmented and to experiment with the different
fragmentation options. For example:

\b
```shell
  % mmpdb smifrag 'c1ccccc1OC'
                     |-------------  variable  -------------|       |---------------------  constant  --------------------
  #cuts | enum.label | #heavies | symm.class | smiles       | order | #heavies | symm.class | smiles           | with-H   
  ------+------------+----------+------------+--------------+-------+----------+------------+------------------+----------
    1   |     N      |    2     |      1     | [*]OC        |    0  |    6     |      1     | [*]c1ccccc1      | c1ccccc1 
    1   |     N      |    6     |      1     | [*]c1ccccc1  |    0  |    2     |      1     | [*]OC            | CO       
    2   |     N      |    1     |     11     | [*]O[*]      |   01  |    7     |     12     | [*]C.[*]c1ccccc1 | -        
    1   |     N      |    1     |      1     | [*]C         |    0  |    7     |      1     | [*]Oc1ccccc1     | Oc1ccccc1
    1   |     N      |    7     |      1     | [*]Oc1ccccc1 |    0  |    1     |      1     | [*]C             | C        
```

Use "`mmpdb fragment`" to fragment a SMILES file and produce a fragment
file for the MMP analysis. Start with the test data file named
"test_data.smi" containing the following structures:

\b
  Oc1ccccc1 phenol  
  Oc1ccccc1O catechol  
  Oc1ccccc1N 2-aminophenol  
  Oc1ccccc1Cl 2-chlorophenol  
  Nc1ccccc1N o-phenylenediamine  
  Nc1cc(O)ccc1N amidol  
  Oc1cc(O)ccc1O hydroxyquinol  
  Nc1ccccc1 phenylamine  
  C1CCCC1N cyclopentanol  

\b
```shell
  % mmpdb fragment test_data.smi -o test_data.fragments
```

Fragmentation can take a while. You can save time by asking the code
to reuse fragmentations from a previous run. If you do that then the
fragment command will reuse the old fragmentation parameters. (You
cannot override them with command-line options.). Here is an example:

\b
```shell
  % mmpdb fragment data_file.smi -o new_data_file.fragments \\
         --cache old_data_file.fragments
```

The "`--cache`" option will greatly improve the fragment performance when
there are only a few changes from the previous run.

The fragmentation algorithm is configured to ignore structures which
are too big or have too many rotatable bonds. There are also options
which change where to make cuts and the number of cuts to make. Use
the "`--help`" option on each command for details.

Use "`mmpdb help-smiles-format`" for details about to parse different
variants of the SMILES file format.


#### 2) Index the MMPA fragments to create a database


The "`mmpa index`" command indexes the output fragments from "`mmpa
fragment`" by their variable fragments, that is, it finds
fragmentations with the same R-groups and puts them together. Here's
an example:

\b
```shell
  % mmpdb index test_data.fragments -o test_data.mmpdb
```

The output from this is a SQLite database.

If you have activity/property data and you do not want the database to
include structures where there is no data, then you can specify
the properties file as well:

\b
```shell
  % mmpdb index test_data.fragments -o test_data.mmpa --properties test_data.csv
```
Use "`mmpdb help-property-format`" for property file format details.

For more help use "`mmpdb index --help`".


#### 3) Add properties to a database


Use "`mmpdb loadprops`" to add or modify activity/property data in the
database. Here's an example property file named 'test_data.csv' with
molecular weight and melting point properties:

\b
  ID      MW      MP  
  phenol  94.1    41  
  catechol        110.1   105  
  2-aminophenol   109.1   174  
  2-chlorophenol  128.6   8  
  o-phenylenediamine      108.1   102  
  amidol  124.1   *  
  hydroxyquinol   126.1   140  
  phenylamine     93.1    -6  
  cyclopentanol   86.1    -19  

The following loads the property data to the MMPDB database file
created in the previous section:

\b
```shell
  % mmpdb loadprops -p test_data.csv test_data.mmpdb
```

Use "`mmpdb help-property-format`" for property file format details.

For more help use "`mmpdb loadprops --help`". Use "`mmpdb list`" to see
what properties are already loaded.

#### 4) Identify possible transforms


Use "`mmpdb transform`" to transform an input structure using the rules
in a database. For each transformation, it can estimate the effect on
any properties. The following looks at possible ways to transform
2-pyridone using the test dataset created in the previous section, and
predict the effect on the "MW" property (the output is reformatted for
clarity):

\b
```shell
  % mmpdb transform --smiles 'c1cccnc1O' test_data.mmpdb --property MW
  ID      SMILES MW_from_smiles MW_to_smiles  MW_radius  \\
   1  Clc1ccccn1         [*:1]O      [*:1]Cl          1
   2   Nc1ccccn1         [*:1]O       [*:1]N          1
   3    c1ccncc1         [*:1]O     [*:1][H]          1

\b
                               MW_fingerprint  MW_rule_environment_id  \\
  tLP3hvftAkp3EUY+MHSruGd0iZ/pu5nwnEwNA+NiAh8                     298
  tLP3hvftAkp3EUY+MHSruGd0iZ/pu5nwnEwNA+NiAh8                     275
  tLP3hvftAkp3EUY+MHSruGd0iZ/pu5nwnEwNA+NiAh8                     267

\b
  MW_count  MW_avg  MW_std  MW_kurtosis  MW_skewness  MW_min  MW_q1  \\
         1    18.5     NaN          NaN          NaN    18.5   18.5
         3    -1.0     0.0          NaN          0.0    -1.0   -1.0
         4   -16.0     0.0          NaN          0.0   -16.0  -16.0

\b
  MW_median  MW_q3  MW_max  MW_paired_t  MW_p_value
       18.5   18.5    18.5          NaN         NaN
       -1.0   -1.0    -1.0  100000000.0         NaN
      -16.0  -16.0   -16.0  100000000.0         NaN
```

This says that "c1cccnc1O" can be transformed to "Clc1ccccn1" using
the transformation \\[\\*:1\\]O>>\\[\\*:1\\]Cl (that is, replace the
oxygen with a chlorine). The best transformation match has a radius
of 1, which includes the aromatic carbon at the attachment point but
not the aromatic nitrogen which is one atom away.

There is only one pair for this transformation, and it predicts a shift
in molecular weight of 18.5. This makes sense as the [OH] is replaced
with a [Cl].

On the other hand, there are three pairs which transform it to
pyridine. The standard deviation of course is 0 because it's a simple
molecular weight calculation. The 100000000.0 is the mmpdb way of
writing "positive infinity".

Melting point is more complicated. The following shows that in the
transformation of 2-pyridone to pyridine there are still 3 matched
pairs and in this case the average shift is -93C with a standard
deviation of 76.727C:

\b
```shell
  % mmpdb transform --smiles 'c1cccnc1O' test_data.mmpdb --property MP
  ID      SMILES MP_from_smiles MP_to_smiles  MP_radius  \\
  1  Clc1ccccn1         [*:1]O      [*:1]Cl          1
  2   Nc1ccccn1         [*:1]O       [*:1]N          1
  3    c1ccncc1         [*:1]O     [*:1][H]          1

\b
                               MP_fingerprint  MP_rule_environment_id  \\
 tLP3hvftAkp3EUY+MHSruGd0iZ/pu5nwnEwNA+NiAh8                     298
 tLP3hvftAkp3EUY+MHSruGd0iZ/pu5nwnEwNA+NiAh8                     275
 tLP3hvftAkp3EUY+MHSruGd0iZ/pu5nwnEwNA+NiAh8                     267

\b
  MP_count  MP_avg  MP_std  MP_kurtosis  MP_skewness  MP_min   MP_q1  \\
        1 -97.000     NaN          NaN          NaN     -97  -97.00
        3 -16.667  75.235         -1.5     -0.33764     -72  -65.75
        3 -93.000  76.727         -1.5      0.32397    -180 -151.00

\b
  MP_median  MP_q3  MP_max  MP_paired_t  MP_p_value
       -97 -97.00     -97          NaN         NaN
       -47  40.00      69       0.3837     0.73815
       -64 -42.25     -35       2.0994     0.17062
```

You might try enabling the "`--explain`" option to see why the algorithm
selected a given tranformation.

For more help use "`mmpdb transform --help`".


#### 5) Use MMP to make a prediction


Use "`mmpdb predict`" to predict the property change in a transformation
from a given reference structure to a given query structure. Use this
when you want to limit the transform results when you know the
starting and ending structures. The following predicts the effect on
molecular weight in transforming 2-pyridone to pyridone:

\b
```shell
  % mmpdb predict --smiles 'c1cccnc1' --reference 'c1cccnc1O' \\
            test_data.mmpdb --property MP
  predicted delta: -93 +/- 76.7268
```

This is the same MP_value and MP_std from the previous section using
'`transform`'.

\b
```shell
  % mmpdb predict --smiles 'c1cccnc1' --reference 'c1cccnc1O' \\
            test_data.mmpdb --property MP --value -41.6
```

I'll redo the calculation with the molecular weight property, and have
mmpdb do the trival calculation of adding the known weight to the
predicted delta:

\b
```shell
  % mmpdb predict --smiles 'c1cccnc1' --reference 'c1cccnc1O' \\
            test_data.mmpdb --property MW --value 95.1
  predicted delta: -16 predicted value: 79.1 +/- 0
```

You might try enabling the "`--explain`" option to see why the algorithm
selected a given transformation, or use "`--save-details`" to save the 
list of possible rules to the file 'pred_detail_rules.txt' and to save 
the list of rule pairs to "pred_detail_pairs.txt".

""")


#### mmpdb help-distributed
@command(name="help-distributed")
def help_distributed():
    "Overview of commands to distribute MMP generation."
    wrap("""
These commands enable MMP generation on a distributed compute cluster,
rather than a single machine.

NOTE: This method does not support properties!

These examples assume you work in a queueing environment with a shared
file system, and a queueing system which lets you submit a command and
a list of filenames, to enqueue the command once for each filename.

This documentation will use the command 'qsub' as a wrapper around [GNU
Parallel](https://www.gnu.org/software/parallel/):

\b
  alias qsub="parallel --no-notice -j 1 --max-procs 4"

This alias suppresses the request to cite GNU parallel in scientific
papers, and has it process one filename at a time, with at most 4
processes in parallel.

I'll pass the filenames to process via stdin, like this example:

\b
  % ls /etc/passwd ~/.bashrc | qsub wc
         2       5      88 /Users/dalke/.bashrc
       120     322    7630 /etc/passwd

This output shows that `wc` received only a single filename because
with two filenames it also shows a 'total' line.

\b
  % wc /etc/passwd ~/.bashrc
       120     322    7630 /etc/passwd
         2       5      88 /Users/dalke/.bashrc
       122     327    7718 total

# Distributed fragmentation generation

The `fragment` command supports multi-processing with the `-j` flag,
which scales to about 4 or 8 processors. For larger data sets you can
break the SMILES dataset into multiple files, fragment each file
indepenently, then merge the results.

These steps are:

\b
  * smi_split - split the SMILES file into smaller files
  * fragment - fragment the each smaller SMILES file into its own fragb file.
  * fragdb_merge - merge the smaller fragdb files together.

## Use smi_split to create N smaller SMILES files

I'll start with a SMILES file containing a header and 20267 SMILES lines:

\b
  % head -3 ChEMBL_CYP3A4_hERG.smi
  SMILES	CMPD_CHEMBLID
  [2H]C([2H])([2H])Oc1cc(ncc1C#N)C(O)CN2CCN(C[C@H](O)c3ccc4C(=O)OCc4c3C)CC2	CHEMBL3612928
  [2H]C([2H])(N[C@H]1C[S+]([O-])C[C@@H](Cc2cc(F)c(N)c(O[C@H](COC)C(F)(F)F)c2)[C@@H]1O)c3cccc(c3)C(C)(C)C	CHEMBL2425617
  % wc -l ChEMBL_CYP3A4_hERG.smi
     20268 ChEMBL_CYP3A4_hERG.smi

By default the "smi_split" command splits a SMILES file into 10
files. (Use `-n` or `--num-files` to change the number of files, or
use `--num-records` to have N records per file.)

\b
  % mmpdb smi_split ChEMBL_CYP3A4_hERG.smi
  Created 10 SMILES files containing 20268 SMILES records.

That "20268 SMILES record" shows that all 20268 lines were used to
generate SMILES records, which is a mistake as it includes the header
line. I'll re-do the command with `--has-header` to have it skip the
header:

\b
  % mmpdb smi_split ChEMBL_CYP3A4_hERG.smi --has-header
  Created 10 SMILES files containing 20267 SMILES records.

By default this generates files which look like:

\b
  % ls -l ChEMBL_CYP3A4_hERG.*.smi
  -rw-r--r--  1 dalke  admin  141307 Nov 15 14:41 ChEMBL_CYP3A4_hERG.0000.smi
  -rw-r--r--  1 dalke  admin  152002 Nov 15 14:41 ChEMBL_CYP3A4_hERG.0001.smi
  -rw-r--r--  1 dalke  admin  127397 Nov 15 14:41 ChEMBL_CYP3A4_hERG.0002.smi
  -rw-r--r--  1 dalke  admin  137930 Nov 15 14:41 ChEMBL_CYP3A4_hERG.0003.smi
  -rw-r--r--  1 dalke  admin  130585 Nov 15 14:41 ChEMBL_CYP3A4_hERG.0004.smi
  -rw-r--r--  1 dalke  admin  150072 Nov 15 14:41 ChEMBL_CYP3A4_hERG.0005.smi
  -rw-r--r--  1 dalke  admin  139620 Nov 15 14:41 ChEMBL_CYP3A4_hERG.0006.smi
  -rw-r--r--  1 dalke  admin  133347 Nov 15 14:41 ChEMBL_CYP3A4_hERG.0007.smi
  -rw-r--r--  1 dalke  admin  131310 Nov 15 14:41 ChEMBL_CYP3A4_hERG.0008.smi
  -rw-r--r--  1 dalke  admin  129344 Nov 15 14:41 ChEMBL_CYP3A4_hERG.0009.smi

The output filenames are determined by the `--template` option, which
defaults to `{prefix}.{i:04}.smi`, where `i` is the output file
index. See `smi_split --help` for details.

## Fragment the SMILES files

These files can be fragmented in parallel:

\b
  % ls ChEMBL_CYP3A4_hERG.*.smi | qsub mmpdb fragment -j 1

I used the `-j 1` flag to have `mmpdb fragment` use only a single
thread, otherwise each of the four fragment commands will use 4
threads even though my laptop only has 4 cores. You should adjust the
value to match the resources available on your compute node.

The `parallel` command doesn't forward output until the program is
done, so it takes a while to see messages like:

\b
  Using 'ChEMBL_CYP3A4_hERG.0002.fragdb' as the default --output file.
  Fragmented record 249/2026 (12.3%)[15:04:16] Conflicting single bond
  directions around double bond at index 5.
  [15:04:16]   BondStereo set to STEREONONE and single bond directions set to NONE.

If no `-o`/`--output` is specified, the `fragment` command uses a
named based on the input name, for example, if the input file is
`ChEMBL_CYP3A4_hERG.0002.smi` then the default output file is
`ChEMBL_CYP3A4_hERG.0002.mmpdb`.

## Merge the fragment files

About 28 minutes later I have 10 fragdb files:

\b
  % ls -l ChEMBL_CYP3A4_hERG.*.fragdb
  -rw-r--r--  1 dalke  admin  13701120 Nov 15 15:12 ChEMBL_CYP3A4_hERG.0000.fragdb
  -rw-r--r--  1 dalke  admin  30453760 Nov 15 15:28 ChEMBL_CYP3A4_hERG.0001.fragdb
  -rw-r--r--  1 dalke  admin  11313152 Nov 15 15:11 ChEMBL_CYP3A4_hERG.0002.fragdb
  -rw-r--r--  1 dalke  admin  12333056 Nov 15 15:11 ChEMBL_CYP3A4_hERG.0003.fragdb
  -rw-r--r--  1 dalke  admin  14024704 Nov 15 15:21 ChEMBL_CYP3A4_hERG.0004.fragdb
  -rw-r--r--  1 dalke  admin  15949824 Nov 15 15:22 ChEMBL_CYP3A4_hERG.0005.fragdb
  -rw-r--r--  1 dalke  admin  19251200 Nov 15 15:26 ChEMBL_CYP3A4_hERG.0006.fragdb
  -rw-r--r--  1 dalke  admin  12759040 Nov 15 15:29 ChEMBL_CYP3A4_hERG.0007.fragdb
  -rw-r--r--  1 dalke  admin   9306112 Nov 15 15:29 ChEMBL_CYP3A4_hERG.0008.fragdb
  -rw-r--r--  1 dalke  admin     20480 Nov 15 15:26 ChEMBL_CYP3A4_hERG.0009.fragdb

I'll merge these with the `fragdb_merge` command:

\b
  % mmpdb fragdb_merge ChEMBL_CYP3A4_hERG.*.fragdb -o ChEMBL_CYP3A4_hERG.fragdb
  Merge complete. #files: 10 #records: 18759 #error records: 1501

This took about 4 seconds.

## Use the merged fragment file as cache

The merged file can be used a a cache file for future fragmentations, such as:

\b
  % ls ChEMBL_CYP3A4_hERG.*.smi | \\
      qsub mmpdb fragment --cache ChEMBL_CYP3A4_hERG.fragdb -j 1

This re-build using cache takes about 20 seconds.

# Distributed indexing

The `mmpdb index` command is single-threaded. It's possible to
parallelize indexing by partitioning the fragments with the same
constant SMILES into their own fragdb data sets, indexing those files,
then merging the results back into a full MMP database.

Note: the merge command can only be used to merge MMP databases with
distinct constants. It cannot be used to merge arbitrary MMP
databases.

Note: the MMP database only stores aggregate information about pair
properties, and the aggregate values cannot be meaningfully merged, so
the merge command will ignore any properties in the database.

## Partitioning on all constants

BEFORE GOING FURTHER, be aware that I've split the SMILES files into
multiple files, fragmented the results into files named
`ChEMBL_CYP3A4_hERG.*.fragdb`, then merged the results back to
`ChEMBL_CYP3A4_hERG.fragdb`. I'm about to partition
`ChEMBL_CYP3A4_hERG.fragdb` into new files also with the pattern
`ChEMBL_CYP3A4_hERG.*.fragdb`. To keep the confusion down, I'll remove
the old files now:

  % rm ChEMBL_CYP3A4_hERG.*.fragdb

You should probably use a naming scheme to keep these two sets of
fragdb files distinct.

The `mmpdb fragdb_partition` command splits a fragment database into N
smaller files. All of the fragmentations with the same constant are in
the same file.

\b
  % mmpdb fragdb_partition ChEMBL_CYP3A4_hERG.fragdb
  Using 467865 constants from database 'ChEMBL_CYP3A4_hERG.fragdb'.
  Exporting 1 constants to 'ChEMBL_CYP3A4_hERG.0000.fragdb' (weight: 334589647)
  Exporting 1 constants to 'ChEMBL_CYP3A4_hERG.0001.fragdb' (weight: 270409141)
  Exporting 1 constants to 'ChEMBL_CYP3A4_hERG.0002.fragdb' (weight: 225664391)
  Exporting 1 constants to 'ChEMBL_CYP3A4_hERG.0003.fragdb' (weight: 117895691)
  Exporting 77977 constants to 'ChEMBL_CYP3A4_hERG.0004.fragdb' (weight: 52836587)
  Exporting 77978 constants to 'ChEMBL_CYP3A4_hERG.0005.fragdb' (weight: 52836587)
  Exporting 77975 constants to 'ChEMBL_CYP3A4_hERG.0006.fragdb' (weight: 52836586)
  Exporting 77976 constants to 'ChEMBL_CYP3A4_hERG.0007.fragdb' (weight: 52836586)
  Exporting 77977 constants to 'ChEMBL_CYP3A4_hERG.0008.fragdb' (weight: 52836586)
  Exporting 77978 constants to 'ChEMBL_CYP3A4_hERG.0009.fragdb' (weight: 52836586)

The command's `--template` option lets you specify how to generate the
output filenames.

Why are there so few constants in first files and so many in the
other? And what are the "weight"s?

I'll use the `fragdb_constants` command to show the distinct constants
in each file and the number of occurrences.

\b
  % mmpdb fragdb_constants ChEMBL_CYP3A4_hERG.0000.fragdb
  constant	N
  *C	25869

That's a lot of methyls (25,869 to be precise).

The indexing command does `N*(N-1)/2` indexing comparisions, plus a
1-cut hydrogen match, so the cost estimate for the methyls is
`25869*(25869-1)/2+1 = 334589647`, which is the `weight` value listed
above.

I'll next list the three most common and least constants in
ChEMBL_CYP3A4_hERG.0004.fragdb:

\b
  % mmpdb fragdb_constants ChEMBL_CYP3A4_hERG.0004.fragdb --limit 3
  constant	N
  *C.*C.*OC	7076
  *C.*Cl	4388
  *C.*C.*CC	3261
  % mmpdb fragdb_constants ChEMBL_CYP3A4_hERG.0004.fragdb | tail -3
  *n1nnnc1SCC(=O)Nc1nc(-c2ccc(Cl)cc2)cs1	1
  *n1nnnc1SCc1nc(N)nc(N2CCOCC2)n1	1
  *n1s/c(=N/C)nc1-c1ccccc1	1

The values of N are much smaller, so the corresponding weight is
significantly smaller.

By default the partition command tries to split the constants evenly
(by weight) across `-n` / `--num-files` files, defaulting to 10, which
combined with the quadratic weighting is why the first few files have
only a single, very common, constant, and why all of the "1" counts
are used to fill space in the remaining files

You can alternatively use `--max-weight` to set an upper
bound for the weights in each file:

\b
  % mmpdb fragdb_partition ChEMBL_CYP3A4_hERG.fragdb --max-weight 50000000
  Exporting 1 constants to 'ChEMBL_CYP3A4_hERG.0000.fragdb' (weight: 334589647)
  Exporting 1 constants to 'ChEMBL_CYP3A4_hERG.0001.fragdb' (weight: 270409141)
  Exporting 1 constants to 'ChEMBL_CYP3A4_hERG.0002.fragdb' (weight: 225664391)
  Exporting 1 constants to 'ChEMBL_CYP3A4_hERG.0003.fragdb' (weight: 117895691)
  Exporting 10 constants to 'ChEMBL_CYP3A4_hERG.0004.fragdb' (weight: 49918518)
  Exporting 11 constants to 'ChEMBL_CYP3A4_hERG.0005.fragdb' (weight: 49916276)
  Exporting 13 constants to 'ChEMBL_CYP3A4_hERG.0006.fragdb' (weight: 49899719)
  Exporting 7 constants to 'ChEMBL_CYP3A4_hERG.0007.fragdb' (weight: 49896681)
  Exporting 43 constants to 'ChEMBL_CYP3A4_hERG.0008.fragdb' (weight: 49893145)
  Exporting 9 constants to 'ChEMBL_CYP3A4_hERG.0009.fragdb' (weight: 49879752)
  Exporting 467768 constants to 'ChEMBL_CYP3A4_hERG.0010.fragdb' (weight: 17615427)

Odds are, you don't want to index the most common fragments. The next
two sections help limits which constants are used.

## Selecting constants

As you saw, the `mmpdb fragdb_constants` command can be used to list
the constants. It can also be used to list a subset of the constants.

The count for each constant quickly decreases to something a bit more
manageable.

\b
  % mmpdb fragdb_constants ChEMBL_CYP3A4_hERG.fragdb --limit 20
  constant	N
  *C	25869
  *C.*C	23256
  *C.*C.*C	21245
  *C.*C.*O	15356
  *C.*O	8125
  *C.*C.*OC	7076
  *C.*OC	6878
  *F	6201
  *C.*F	6198
  *C.*c1ccccc1	5124
  *C.*O.*O	5117
  *c1ccccc1	5073
  *OC	4944
  *Cl	4436
  *C.*Cl	4388
  *O	4300
  *F.*F	4281
  *C.*F.*F	3935
  *C.*C.*F	3656
  *F.*F.*F	3496

I'll select those constants which occur only 2,000 matches or fewer,
and limit the output to the first 5.

  % mmpdb fragdb_constants ChEMBL_CYP3A4_hERG.fragdb --max-count 2000 --limit 5
  constant	N
  *C.*CC.*O	1954
  *C.*C(F)(F)F	1915
  *C.*C.*OC(C)=O	1895
  *C(F)(F)F	1892
  *Cl.*Cl	1738

or count the number of constants which only occur once (the 1-cut
constants might match with a hydrogen substitution while the others
will never match). I'll use `--no-header` so the number of lines of
output matches the number of constants:

  % mmpdb fragdb_constants ChEMBL_CYP3A4_hERG.fragdb --max-count 1 --no-header | wc -l
    370524

These frequent constants are for small fragments. I'll limit the
selection to constants where each part of the constant has at least 5
heavy atoms:

\b
  % mmpdb fragdb_constants ChEMBL_CYP3A4_hERG.fragdb --min-heavies-per-const-frag 5 --limit 4
  constant	N
  *c1ccccc1	5073
  *c1ccccc1.*c1ccccc1	1116
  *Cc1ccccc1	1050
  *c1ccc(F)cc1	921

I'll also require `N` be between 10 and 1000.

\b 
  % mmpdb fragdb_constants ChEMBL_CYP3A4_hERG.fragdb --min-heavies-per-const-frag 5 \\
     --min-count 10 --max-count 1000 --no-header | wc -l
  1940

That's a much more tractable size for this example.

## Partitioning on selected constants

Before going futher, I'm going to clear out any old files which might
have been generated by the above commands:

  % rm ChEMBL_CYP3A4_hERG.*.fragdb

As you saw earlier, the `mmpdb fragdb_partition` command by default
partitions on all constants. Alternatively, use the `--constants` flag
to pass in a list of constants to use. This can be a file name, or `-`
to accept constants from stdin, as in the following three lines:

\b
  % mmpdb fragdb_constants ChEMBL_CYP3A4_hERG.fragdb --min-heavies-per-const-frag 5 \\
       --min-count 10 --max-count 1000 | \\
       mmpdb fragdb_partition ChEMBL_CYP3A4_hERG.fragdb --constants -
  Using 1940 constants from file '<stdin>'.
  Exporting 1 constants to 'ChEMBL_CYP3A4_hERG.0000.fragdb' (weight: 423661)
  Exporting 1 constants to 'ChEMBL_CYP3A4_hERG.0001.fragdb' (weight: 382376)
  Exporting 109 constants to 'ChEMBL_CYP3A4_hERG.0002.fragdb' (weight: 382044)
  Exporting 261 constants to 'ChEMBL_CYP3A4_hERG.0003.fragdb' (weight: 382013)
  Exporting 261 constants to 'ChEMBL_CYP3A4_hERG.0004.fragdb' (weight: 382013)
  Exporting 260 constants to 'ChEMBL_CYP3A4_hERG.0005.fragdb' (weight: 382010)
  Exporting 261 constants to 'ChEMBL_CYP3A4_hERG.0006.fragdb' (weight: 382010)
  Exporting 262 constants to 'ChEMBL_CYP3A4_hERG.0007.fragdb' (weight: 382010)
  Exporting 262 constants to 'ChEMBL_CYP3A4_hERG.0008.fragdb' (weight: 382009)
  Exporting 262 constants to 'ChEMBL_CYP3A4_hERG.0009.fragdb' (weight: 382003)

Note: the `--constants` parser expects the first line to be a header,
which is why I don't use `--no-header` in the `fragdb_constants`
command. Alternatively, also use `--no-header` in the
`fragdb_partition` command if the input does not have a header.

## Indexing in parallel

The partitioned fragdb files can be indexed in parallel:

\b
  % ls ChEMBL_CYP3A4_hERG.*.fragdb | qsub mmpdb index
  WARNING: No --output filename specified. Saving to 'ChEMBL_CYP3A4_hERG.0000.mmpdb'.
  WARNING: No --output filename specified. Saving to 'ChEMBL_CYP3A4_hERG.0001.mmpdb'.
  WARNING: No --output filename specified. Saving to 'ChEMBL_CYP3A4_hERG.0002.mmpdb'.
  WARNING: No --output filename specified. Saving to 'ChEMBL_CYP3A4_hERG.0003.mmpdb'.
  WARNING: No --output filename specified. Saving to 'ChEMBL_CYP3A4_hERG.0004.mmpdb'.
  WARNING: No --output filename specified. Saving to 'ChEMBL_CYP3A4_hERG.0005.mmpdb'.
  WARNING: No --output filename specified. Saving to 'ChEMBL_CYP3A4_hERG.0006.mmpdb'.
  WARNING: No --output filename specified. Saving to 'ChEMBL_CYP3A4_hERG.0007.mmpdb'.
  WARNING: No --output filename specified. Saving to 'ChEMBL_CYP3A4_hERG.0008.mmpdb'.
  WARNING: No --output filename specified. Saving to 'ChEMBL_CYP3A4_hERG.0009.mmpdb'.

(If you don't like these warning messages, use the `--quiet` flag.)

## Merging partitioned mmpdb files

The last step is to merge the partitioned mmpdb files with the `merge`
option, which only works if no two mmpdb files share the same constant:

\b
  % mmpdb merge ChEMBL_CYP3A4_hERG.*.mmpdb -o ChEMBL_CYP3A4_hERG.mmpdb

Let's take a look:

\b
  % mmpdb list ChEMBL_CYP3A4_hERG.mmpdb
            Name           #cmpds #rules #pairs #envs  #stats  |-------- Title --------| Properties
  ChEMBL_CYP3A4_hERG.mmpdb   4428  21282 203856 143661      0  Merged MMPs from 10 files <none>



""")

#### mmpdb help-smiles
@command(name="help-smiles-format")
def help_smiles_format():
    "description of the SMILES file parsing options"
    click.echo("""
This help topic explains how the "--delimiter" and "--has-header"
options  of the "mmpa fragment" command affect SMILES parsing.

The mmpa code support the most common variants of a SMILES file. Every
SMILES file stores line-oriented records, with the SMILES in the first
field and the id (also called the title) in the second field. However,
there are differences in how to handle the first line of the file, and
in how to distinguish which is the second field. Some people use the
first line to store a header for each column in the file.

The classic Daylight SMILES file had no header line and interprets the
each line as a SMILES string followed by a whitespace followed by the
id/title. The id is the rest of the line, which means it may include
space and tabs. This is useful if you have identifiers with a space
in them, like IUPAC names or common names like "vitamin D".

A common variant is to treat the SMILES file as a CSV file, that is,
with at least two columns separated by a space, tab, or whitespace
character. Columns beyond the second column are ignored.

Use the "--delimiter" option to specify the delimiter type. The
available delimiter values are:

  "whitespace" (default) - CSV file with one or more whitespace
      characters as the delimiter
  "space" - CSV file with the space character as the delimiter
  "tab" - CSV file with the tab character as the delimiter
  "to-eol" - follow the Daylight rule where the id is
      everything past the first whitespace character
  "comma" - CSV file with a comma character as the delimiter
      (this is a very non-standard SMILES file format!)

The "native" delimiter is for chemfp compatibility. It is equivalent
to "whitespace", which matches the native RDKit parsing style.

Another variant takes the CSV format one step further, and lists
column headers as the first line of the file. The mmpa code will
ignore that line if you add the "--has-header" option.

Example command-line parameters:
   --delimiter whitespace       -- the default uses one or more whitespace
                                    as the column delimiter
   --delimiter to-eol           -- Daylight-style SMILES format
   --delimiter tab --has-header -- tab-delimited CSV, with a header line

""")

    
#### mmpdb help-properties-format
@command(name="help-property-format")
def help_property_format():
    "description of the property file format"
    click.echo("""
This describes the file format used by the --properties option of
"mmpdb index" and "mmpdb loadprops" commands.

A property file contains information about the physical properties or
activity associated with a compound id. It is formatted as a data
table, where each line of the file is a row in the table. The first
line contains columns names. Each line contains exactly N fields, with
one field per column. The fields should be tab-separated. If the line
does not contain a tab character then it will be interpreted as
whitespace separated fields.

The first column contains compound identifiers. It must have the
column name "id", "ID", "Name", or "name". The remaining columns are
property columns, with the property name in the first row and property
values in the remaining rows. The property value for a given
identifier and property name must either be a number (something which
can be parsed as a floating point value; this includes integers) or
the symbol "*" to indicates that the value is missing.

Here is an example property file:

  ID MP CHR1 CHR2
  GEJYOJ 3 71 31.3
  ACIDUL 5 65 67.2
  KIXRIS 5 * *
  SOFWIV01 5 83 79.3

It defines three properties - MP, CHR1, and CHR2 - for four
identifiers. The MP value of GEJYOJ is 3, which is interpreted as
3.0. The CHR2 value of ACIDUL is interpted as 67.2. Compound KIXRIS
has the MP property 5.0 but the "*" indicates that its CHR1 and CHR2
properties are not known.

""")
#### mmpdb help-admin
@command(name="help-admin")
def help_admin():
    "overview on how to use administor an mmpdb database"
    click.echo("""

The administrative commands are:
  * fragdb_list: summarize fragment database (".fragdb") contents
  * list: summarize MMP database (".mmpdb") contents
  * loadprops: add or modify property information
  * smicat: list the structures in a fragment or MMP database
  * rulecat: list the rules in an MMP database
  * propcat: show the properties in an MMP database
  * drop_index: drop the MMP database indices
  * create_index: (re)create the MMP database indices

See the --help options for each command for more details.
""")
