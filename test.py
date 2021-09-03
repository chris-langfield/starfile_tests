 
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

os.system('rm -f saved_*.star')

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

os.system('rm -f gemmi/saved_*')
