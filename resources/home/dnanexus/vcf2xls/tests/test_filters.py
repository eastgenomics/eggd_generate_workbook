import argparse
from multiprocessing.managers import ValueProxy
import os
from random import shuffle
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.abspath(
    os.path.join(os.path.realpath(__file__), '../../')
))

from utils.columns import splitColumns
from utils.filters import filter
from utils.vcf import vcf
from tests import TEST_DATA_DIR

# initialise vcf class that contains functions for parsing header
vcf_handler = vcf(argparse.Namespace)



class TestFilters():
    """
    Tests for building and applying filters from filters.py to dataframe(s)
    of variants
    """
    def read_vcf(self):
        """
        Read in vcf with valid argparse NameSpace for testing, call in every
        test function to reset up unmodified vcf to test each method on

        Returns
        -------
        vcf_handler : utils.vcf.vcf
            class instance of vcf from utils
        """
        # test data vcf
        columns_vcf = os.path.join(TEST_DATA_DIR, "NA12878_unittest.vcf")

        # initialise vcf class with a valid argparse input to allow
        # calling .read()
        vcf_handler = vcf(argparse.Namespace(
            add_name=True, analysis='',
            filter=None, keep=False, merge=False,
            reorder=[], exclude=None, include=None,
            out_dir='', output='', always_keep=pd.DataFrame(),
            panel='', print_columns=False, reads='', rename=None,
            sample='', sheets=['variants'], summary=None, usable_reads='',
            vcfs=[columns_vcf], workflow=('', '')
        ))
        vcf_df, csq_fields = vcf_handler.read(columns_vcf)

        # call methods like in vcf.read() to process df and add to self
        vcf_df, expanded_vcf_rows = splitColumns.csq(vcf_df, csq_fields)
        vcf_df = splitColumns.info(vcf_df)
        vcf_df = splitColumns.format_fields(vcf_df)

        # set correct dtypes, required for setting numeric & object types
        # to ensure correct filtering filtering
        vcf_df = vcf_handler.set_types(vcf_df)
        vcf_handler.vcfs.append(vcf_df)

        return vcf_handler

    @staticmethod
    def get_random_column_value(column):
        """
        Give a dataframe column, return a random non-NA value

        Parameters
        ----------
        column : pd.Series
            column of dataframe to get random value from

        Returns
        -------
        value : int | string
            random value from column
        """
        values = column.tolist()
        shuffle(values)
        return [x for x in values if not pd.isna(x)][0]


    def test_building_filters(self):
        """
        Test filters passed to args are correctly built
        """
        vcf_handler = self.read_vcf()

        # set some example filters as passed to args
        vcf_handler.args.filter = [
            "CHROM==5", "gnomAD_AF>0.02", "Consequence!=missense_variant",
            "AN<2", "ReadPosRankSum<=0.1", "FS>=4"
        ]

        # the above should be turned into a list of lists, with column,
        # operand and value as separate elements
        correct_filter_format = [
            ["CHROM", "==", "5"], ["gnomAD_AF", ">", "0.02"],
            ["Consequence", "!=", "missense_variant"], ["AN", "<", "2"],
            ["ReadPosRankSum", "<=", "0.1"], ["FS", ">=", "4"]
        ]

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()

        assert filter_handler.filters == correct_filter_format, (
            "Filters incorrectly parsed with filters.build()"
        )


    def test_keep_argument_adds_extra_df_filtered_rows(self):
        """
        Tests that when --keep is passed, the filtered rows are saved to the
        last dataframe in self.vcfs and sheets list has "filtered" appended
        """
        vcf_handler = self.read_vcf()
        vcf_handler.args.filter = ["CHROM==chr17"]
        vcf_handler.args.keep = True

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()
        filter_handler.filter()


        # check sheets name added to list of names
        assert filter_handler.args.sheets[-1] == "filtered", (
            "sheets list does not have 'filtered' added with --keep passed"
        )

        assert len(filter_handler.vcfs) == 2, (
            'filtered variants df not retained when args.keep specified'
        )


    def test_correct_rows_filtered_with_eq(self):
        """
        Test when using equal operator filter is correctly applied
        """
        vcf_handler = self.read_vcf()

        # get random value from column to test filtering on
        value = self.get_random_column_value(vcf_handler.vcfs[0]['CHROM'])

        vcf_handler.args.filter = [f"CHROM=={value}"]
        vcf_handler.args.keep = True

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()
        filter_handler.filter()

        assert filter_handler.vcfs[0]['CHROM'].unique().tolist() == [value], (
            "Filtering with '==' operator returned incorrect rows"
        )

        assert all([
            x != [value] for x in filter_handler.vcfs[-1]['CHROM'].tolist()
        ]), (
            "Filtering with '==' operator filtered incorrect rows"
        )


    def test_correct_rows_filtered_with_not_eq(self):
        """
        Test when using not equal operator filter is correctly applied
        """
        vcf_handler = self.read_vcf()

        # get random value from column to test filtering on
        value = self.get_random_column_value(vcf_handler.vcfs[0]['CHROM'])

        vcf_handler.args.filter = [f"CHROM!={value}"]
        vcf_handler.args.keep = True

        total_rows_before_filter = len(vcf_handler.vcfs[0].index)

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()
        filter_handler.filter()

        total_rows_after_filter = sum([len(x.index) for x in filter_handler.vcfs])

        # check no rows dropped
        assert total_rows_after_filter == total_rows_before_filter, (
            "Mismatch between total rows before and after filtering"
        )

        # check filtered df only has no selected chromosome variants
        assert filter_handler.vcfs[-1]['CHROM'].unique().tolist() == [value], (
            "Filtering with '!=' did not filter out all rows"
        )

        # check dataframe has no selected chromosome variants
        assert all([
            x != [value] for x in filter_handler.vcfs[0]['CHROM'].tolist()
        ]), (
            "Filtering with '!=' filtered out incorrect rows"
        )


    def test_correct_rows_filtered_with_gt(self):
        """
        Tests the correct rows are filtered with one filter applied, and no
        rows are dropped
        """
        vcf_handler = self.read_vcf()

        # get random value from column to test filtering on
        value = self.get_random_column_value(vcf_handler.vcfs[0]['DP'])

        vcf_handler.args.filter = [f"DP>{value}"]
        vcf_handler.args.keep = True

        total_rows_before_filter = len(vcf_handler.vcfs[0].index)

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()
        filter_handler.filter()

        total_rows_after_filter = sum([len(x.index) for x in filter_handler.vcfs])

        # check no rows dropped
        assert total_rows_after_filter == total_rows_before_filter, (
            "Mismatch between total rows before and after filtering"
        )

        assert all([x > value for x in filter_handler.vcfs[0]['DP'].tolist()]), (
            'Rows not filtered out when filtering with > DP'
        )

        assert all([x <= value for x in filter_handler.vcfs[-1]['DP'].tolist()]), (
            "Incorrect rows filtered out when filtering with > DP"
        )


    def test_correct_rows_filtered_with_gt_eq(self):
        """
        Tests the correct rows are filtered with one filter applied, and no
        rows are dropped
        """
        vcf_handler = self.read_vcf()

        # get random value from column to test filtering on
        value = self.get_random_column_value(vcf_handler.vcfs[0]['DP'])

        vcf_handler.args.filter = [f"DP>={value}"]
        vcf_handler.args.keep = True

        total_rows_before_filter = len(vcf_handler.vcfs[0].index)

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()
        filter_handler.filter()

        total_rows_after_filter = sum([len(x.index) for x in filter_handler.vcfs])

        # check no rows dropped
        assert total_rows_after_filter == total_rows_before_filter, (
            "Mismatch between total rows before and after filtering"
        )

        assert all([x >= value for x in filter_handler.vcfs[0]['DP'].tolist()]), (
            'Rows not filtered out when filtering with >= on DP'
        )

        assert all([x < value for x in filter_handler.vcfs[-1]['DP'].tolist()]), (
            "Incorrect rows filtered out when filtering with > on DP"
        )


    def test_correct_rows_filtered_with_lt(self):
        """
        Tests the correct rows are filtered with one filter applied, and no
        rows are dropped
        """
        vcf_handler = self.read_vcf()

        # get random value from column to test filtering on
        value = self.get_random_column_value(vcf_handler.vcfs[0]['gnomAD_AF'])

        vcf_handler.args.filter = [f"gnomAD_AF<{value}"]
        vcf_handler.args.keep = True

        total_rows_before_filter = len(vcf_handler.vcfs[0].index)

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()
        filter_handler.filter()

        total_rows_after_filter = sum([len(x.index) for x in filter_handler.vcfs])

        # check no rows dropped
        assert total_rows_after_filter == total_rows_before_filter, (
            "Mismatch between total rows before and after filtering"
        )

        # everything should be under filter value or NaN
        assert all([
            x < value or pd.isna(x) for x in filter_handler.vcfs[0]['gnomAD_AF'].tolist()
        ]), (
            'Rows not filtered out when filtering with gnomAD_AF < 0.02'
        )

        assert all([
            x >= value for x in filter_handler.vcfs[-1]['gnomAD_AF'].tolist()
        ]), (
            "Incorrect rows filtered out when filtering with < on gnomAD_AF"
        )


    def test_correct_rows_filtered_with_lt_eq(self):
        """
        Tests the correct rows are filtered with one filter applied, and no
        rows are dropped
        """
        vcf_handler = self.read_vcf()

        # get random value from column to test filtering on
        value = self.get_random_column_value(vcf_handler.vcfs[0]['gnomAD_AF'])

        vcf_handler.args.filter = [f"gnomAD_AF<={value}"]
        vcf_handler.args.keep = True

        total_rows_before_filter = len(vcf_handler.vcfs[0].index)

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()
        filter_handler.filter()

        total_rows_after_filter = sum([len(x.index) for x in filter_handler.vcfs])

        # check no rows dropped
        assert total_rows_after_filter == total_rows_before_filter, (
            "Mismatch between total rows before and after filtering"
        )

        # everything should be under filter value or NaN
        assert all([
            x <= value or pd.isna(x) for x in filter_handler.vcfs[0]['gnomAD_AF'].tolist()
        ]), (
            'Rows not filtered out when filtering with gnomAD_AF < 0.02'
        )

        assert all([
            x > value for x in filter_handler.vcfs[-1]['gnomAD_AF'].tolist()
        ]), (
            "Incorrect rows filtered out when filtering with <= on gnomAD_AF"
        )


    def test_correct_rows_filtered_w_two_filters_diff_columns(self):
        """
        Tests the correct rows are filtered with two filter applied, rows are
        not double counted and filtered twice and no rows are dropped
        """
        print('testing 2 filters')
        vcf_handler = self.read_vcf()

        # get random values from columns to test filtering on
        dp_value = self.get_random_column_value(vcf_handler.vcfs[0]['DP'])
        qual_value = self.get_random_column_value(vcf_handler.vcfs[0]['QUAL'])

        vcf_handler.args.filter = [f"DP>{dp_value}", f"QUAL<{qual_value}"]
        vcf_handler.args.keep = True

        total_rows_before_filter = len(vcf_handler.vcfs[0].index)

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()
        filter_handler.filter()

        total_rows_after_filter = sum([len(x.index) for x in filter_handler.vcfs])

        # check no rows dropped or duplicated
        assert total_rows_after_filter == total_rows_before_filter, (
            "Mismatch between total rows before and after filtering"
        )


        # check everything should be at filter value for DP and MPOS
        assert all([
            x > dp_value or y < qual_value for x, y in zip(
                filter_handler.vcfs[0]['DP'].tolist(),
                filter_handler.vcfs[0]['QUAL'].tolist()
            )
        ]), (
            'Rows not filtered out when filtering with 2 filters'
        )

        assert all([
            x <= dp_value or y >= qual_value for x, y in zip(
                filter_handler.vcfs[-1]['DP'].tolist(),
                filter_handler.vcfs[-1]['QUAL'].tolist()
            )
        ]), (
            'Incorrect rows filtered out when filtering with 2 filters'
        )


    def test_correct_rows_filtered_w_two_filters_same_column(self):
        """
        Tests the correct rows are filtered with two filter applied on the
        column, rows are not double counted and filtered twice and no rows
        are dropped
        """
        vcf_handler = self.read_vcf()

        vcf_handler.args.filter = [
            "Consequence!=synonymous_variant",
            "Consequence!=3_prime_UTR_variant"
        ]
        vcf_handler.args.keep = True

        total_rows_before_filter = len(vcf_handler.vcfs[0].index)

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()
        filter_handler.filter()

        total_rows_after_filter = sum([len(x.index) for x in filter_handler.vcfs])

        # check no rows dropped or duplicated
        assert total_rows_after_filter == total_rows_before_filter, (
            "Mismatch between total rows before and after filtering"
        )

        # check everything should be at filter value for DP and MPOS
        assert all([
            x != "3_prime_UTR_variant" or x != "synonymous_variant" \
            for x in filter_handler.vcfs[0]['Consequence'].tolist()
        ]), (
            'Rows not filtered out when filtering with 2 filters on same column'
        )

        assert sorted(filter_handler.vcfs[-1]['Consequence'].unique().tolist()) == [
            "3_prime_UTR_variant", "synonymous_variant"
        ], (
            'Incorrect rows filtered out when filtering with 2 filters on same column'
        )


    def test_correct_rows_filtered_w_many_filters(self):
        """
        Tests the correct rows are filtered with multiple filters across
        multiple columns
        """
        vcf_handler = self.read_vcf()

        vcf_handler.args.filter = [
            "Consequence!=synonymous_variant",
            "Consequence!=3_prime_UTR_variant",
            "Consequence!=intron_variant",
            "gnomAD_AF<0.02",
            "gnomADg_AF<0.02",
            "QUAL>2000",
            "AC==1"
        ]
        vcf_handler.args.keep = True

        total_rows_before_filter = len(vcf_handler.vcfs[0].index)

        filter_handler = filter(vcf_handler.args, vcf_handler.vcfs)
        filter_handler.build()
        filter_handler.filter()

        total_rows_after_filter = sum([len(x.index) for x in filter_handler.vcfs])

        # check no rows dropped or duplicated
        assert total_rows_after_filter == total_rows_before_filter, (
            "Mismatch between total rows before and after filtering"
        )

        for _, row in filter_handler.vcfs[0].iterrows():
            # check values of retained df rows
            assert row['Consequence'] != 'synonymous_variant' or \
                row['Consequence'] != '3_prime_UTR_variant' or \
                row['Consequence'] != 'intron_variant' or \
                row['gnomAD_AF'] <= 0.02 or \
                row['gnomADg_AF'] <= 0.02 or \
                row['QUAL'] > 2000 or \
                row['AC'] == 1, (
                    "Multiple combined filters have not filtered out correct rows"
                )

        # check values of filtered out df rows
        for _, row in filter_handler.vcfs[0].iterrows():
            assert row['Consequence'] == 'synonymous_variant' or \
                row['Consequence'] == '3_prime_UTR_variant' or \
                row['Consequence'] == 'intron_variant' or \
                row['gnomAD_AF'] > 0.02 or \
                row['gnomADg_AF'] > 0.02 or \
                row['QUAL'] <= 2000 or \
                row['AC'] != 1, (
                    "Multiple combined filters have wrongly filtered out rows"
                )



if __name__ == "__main__":
    t = TestFilters()
    t.read_vcf()
    t.test_building_filters()
    t.test_correct_rows_filtered_with_eq()
    t.test_correct_rows_filtered_with_not_eq()
    t.test_correct_rows_filtered_with_gt()
    t.test_keep_argument_adds_extra_df_filtered_rows()
    t.test_correct_rows_filtered_with_gt_eq()
    t.test_correct_rows_filtered_with_lt()
    t.test_correct_rows_filtered_with_lt_eq()
    t.test_correct_rows_filtered_w_two_filters_same_column()
    t.test_correct_rows_filtered_w_many_filters()
