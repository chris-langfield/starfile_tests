# starfile_tests

#### Unexpected behavior with single-row blocks following other blocks in a STAR file

Hi `starfile` authors, we are planning to use your library in our package. When building some tests, we encountered the following issue. We're wondering whether this is a bug or whether we are possibly using the library wrong. Thanks!

#### Description

When reading in STAR files, blocks which are

- comprised of a single row of data (whether stored as a loop_ or not)
- not the *first* block of the file

exhibit unexpected behavior when read from a file, written back, and then read back again.

It seems that some data from the preceding block is copied in. For example with the following STAR file:


```
data_block_0

loop_
_val1
_val2
_val3
1.0     2.0     3.0


data_block_1

loop_
_col1
_col2
_col3
A       B       C
```
When then file is read, written, and then read back, we get the following dataframes:

```
block_0
ORIGINAL
   val1  val2  val3
0   1.0   2.0   3.0
NEW
   val1  val2  val3
0   1.0   2.0   3.0

block_1
ORIGINAL
  col1 col2 col3
0    A    B    C
NEW
   val1  val2  val3 col1 col2 col3
0   1.0   2.0   3.0    A    B    C
```

As can be seen above, some data from `block_0` is incorporated into `block_1`

#### Comparison with GEMMI - sanity check

To ensure we weren't using pathological STAR files, we attempted the same process using `starfile` and `gemmi.cif`. We used several simple example STAR files, including some from the `tests/data` path in the `starfile` directory. 

The following python script tests a few cases:

```python
import starfile
import pandas as pd
import os
from gemmi import cif

files = ['example_with_loops.star', 'example_no_loops.star', 'example_mixed_1.star', 'example_mixed_2.star', 'example_nonconsecutive.star', 'example_nonconsecutive_2.star', 'single_line_end_of_multiblock.star', 'single_line_middle_of_multiblock.star']

print('starfile package tests')
print('----------------------')
for f in files:
    orig = starfile.read(f, always_dict=True)

    starfile.write(orig, f"saved_{f.replace('.star','')}.star", overwrite=True)

    compare = starfile.read(f"saved_{f.replace('.star','')}.star", always_dict=True)

    print(f)
    good = True
    for key, df in orig.items():
        print(key)
        print('ORIGINAL')
        print(df)
        print('NEW')
        print(compare[key])
        print()
        if not compare[key].equals(orig[key]):
            good = False
            break
    if good:
        print('success!')
    else:
        print('comparison failed')
    print()

print()

print('GEMMI comparison w/ same files')
print('---------------------------')
for f in files:
    print(f)

    # read file, write out same object, and read it back
    orig = cif.read_file('gemmi/' + f)
    orig.write_file('gemmi/saved_' + f)
    compare = cif.read_file('gemmi/saved_' + f)

    # make sure they have the same number of blocks
    assert(len(orig) == len(compare))
    for block in orig:

        # get block name and find corresponding block in compare
        orig_block = block
        compare_block = compare[block.name]

        # iterate over items in block. these can be a pair or a loop
        for item in orig_block:
            if item.pair is not None:
                orig_pair = item.pair
                # find the corresponding pair in the compare block
                compare_pair = compare_block.find_pair(item.pair[0])
                # compare each pair and make sure they are equal
                assert(orig_pair == compare_pair)
                # make sure that if this block has pairs, it doesn't also
                # have a loop
                assert(item.loop is None)
            if item.loop is not None:
                orig_loop = item.loop
                # find the coresponding loop in the compare block
                compare_loop = compare_block.find_loop_item(orig_loop.tags[0]).loop

                # make sure the loops have the same tags
                assert(orig_loop.tags == compare_loop.tags)

                for tag in orig_loop.tags:
                    orig_col = orig_block.find_values(tag)
                    compare_col = compare_block.find_values(tag)
                    # make sure columns have same lengths
                    assert(len(orig_col) == len(compare_col))
                    # make sure columns are equal by index
                    for i in range(len(orig_col)):
                        assert(orig_col[i] == compare_col[i])

                # make sure that if this block has a loop, it doesn't also
                # have pairs
                assert(item.pair is None)
    print('success!')
    print()

```
We get the following output:

```

starfile package tests
----------------------
example_with_loops.star
block_0
ORIGINAL
   val1  val2  val3
0   1.0   2.0   3.0
NEW
   val1  val2  val3
0   1.0   2.0   3.0

block_1
ORIGINAL
  col1 col2 col3
0    A    B    C
NEW
   val1  val2  val3 col1 col2 col3
0   1.0   2.0   3.0    A    B    C

comparison failed

example_no_loops.star
block_0
ORIGINAL
   val1  val2  val3
0   1.0   2.0   3.0
NEW
   val1  val2  val3
0   1.0   2.0   3.0

block_1
ORIGINAL
   val1  val2  val3 col1 col2
0   1.0   2.0   3.0    A    B
NEW
   val1  val2  val3 col1 col2
0   1.0   2.0   3.0    A    B

success!

example_mixed_1.star
block_0
ORIGINAL
   val1  val2  val3
0   1.0   2.0   3.0
NEW
   val1  val2  val3
0   1.0   2.0   3.0

block_1
ORIGINAL
    .0 col1 col2
0  2.0    A    B
NEW
   val1  val2  val3   .0 col1 col2
0   1.0   2.0   3.0  2.0    A    B

comparison failed

example_mixed_2.star
block_0
ORIGINAL
   val1  val2  val3
0   1.0   2.0   3.0
NEW
   val1  val2  val3
0   1.0   2.0   3.0

block_1
ORIGINAL
  col1 col2 col3
0    A    B    C
NEW
   val1  val2  val3 col1 col2 col3
0   1.0   2.0   3.0    A    B    C

comparison failed

example_nonconsecutive.star
block_0
ORIGINAL
   val1  val2  val3
0   1.0   2.0   3.0
NEW
   val1  val2  val3
0   1.0   2.0   3.0

block_inbetween
ORIGINAL
  d1 d2 d3
0  a  b  c
1  d  e  f
2  g  h  i
NEW
  d1 d2 d3
0  a  b  c
1  d  e  f
2  g  h  i

block_1
ORIGINAL
  col1 col2 col3
0    A    B    C
NEW
     col1 col2 col3
0  h    A    B    C

comparison failed

example_nonconsecutive_2.star
block_inbetween
ORIGINAL
  d1 d2 d3
0  a  b  c
1  d  e  f
2  g  h  i
NEW
  d1 d2 d3
0  a  b  c
1  d  e  f
2  g  h  i

block_1
ORIGINAL
  col1 col2 col3
0    A    B    C
NEW
     col1 col2 col3
0  h    A    B    C

comparison failed

single_line_end_of_multiblock.star
block_1
ORIGINAL
                     rlnImageName  ... rlnCoordinateZ
0  000001@0001_sum_particles.mrcs  ...       -51.5227
1  000001@0001_sum_particles.mrcs  ...       -51.5227

[2 rows x 5 columns]
NEW
                     rlnImageName  ... rlnCoordinateZ
0  000001@0001_sum_particles.mrcs  ...       -51.5227
1  000001@0001_sum_particles.mrcs  ...       -51.5227

[2 rows x 5 columns]

block_3
ORIGINAL
                     rlnImageName  ... rlnCoordinateZ
0  000001@0001_sum_particles.mrcs  ...       -51.5227

[1 rows x 5 columns]
NEW
  00001@0001_sum_particles.mrcs  ... rlnCoordinateZ
0                  0002_sum.mrc  ...       -51.5227

[1 rows x 6 columns]

comparison failed

single_line_middle_of_multiblock.star
block_1
ORIGINAL
                     rlnImageName  ... rlnCoordinateZ
0  000001@0001_sum_particles.mrcs  ...       -51.5227

[1 rows x 5 columns]
NEW
                     rlnImageName  ... rlnCoordinateZ
0  000001@0001_sum_particles.mrcs  ...       -51.5227

[1 rows x 5 columns]

block_3
ORIGINAL
                    rlnImageName0  ... rlnCoordinateZ0
0  000001@0001_sum_particles.mrcs  ...        -51.5227

[1 rows x 5 columns]
NEW
                     rlnImageName  ... rlnCoordinateZ0
0  000001@0001_sum_particles.mrcs  ...        -51.5227

[1 rows x 10 columns]

comparison failed


GEMMI comparison w/ same files
---------------------------
example_with_loops.star
success!

example_no_loops.star
success!

example_mixed_1.star
success!

example_mixed_2.star
success!

example_nonconsecutive.star
success!

example_nonconsecutive_2.star
success!

single_line_end_of_multiblock.star
success!

single_line_middle_of_multiblock.star
success!


```
