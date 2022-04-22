import argparse
import os
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.append(os.path.abspath(
    os.path.join(os.path.realpath(__file__), '../../')
))

from utils.vcf import vcf
from utils.columns import splitColumns
from tests import TEST_DATA_DIR


def read_test_vcf(vcf_file):
    """
    Read in test vcf to dataframe using methods from vcf()
    """
    # initialise vcf class with a valid argparse input to allow calling .read()
    vcf_handler = vcf(argparse.Namespace(
        add_name=False, analysis='', clinical_indication='', exclude=None,
        filter=None, include=None, keep=False, merge=False,
        out_dir='',
        output='',
        panel='', print_columns=False, print_header=False, reads='',
        rename=None, reorder=None, sample='', sheets=['variants'],
        summary=None, usable_reads='', vcfs=[vcf_file], workflow=('', '')
    ))
    vcf_df = vcf_handler.read(vcf_file)

    return vcf_df


class TestInfoColumn():
    """
    Tests for splitColumns.info() that splits out key value pairs
    from INFO column to separate columns in dataframe
    """
    test_vcf = f"{TEST_DATA_DIR}/NA12878_unittest.split.vcf"

    # run dataframe through splitColumns.info() to split out INFO column
    vcf_df = read_test_vcf(vcf_file=test_vcf)
    vcf_df = splitColumns().split(vcf_df)


    def test_parsed_correct_columns_from_info_records(self) -> None:
        """
        Test that all unique INFO values from all rows correctly parsed and
        set to columns in returned dataframe
        """
        # read all the INFO keys direct from vcf
        output = subprocess.run(
            (
                f"cut -f8 {self.test_vcf} | grep -oh "
                f"';[A-Za-z0-9\_\-\.]*=' | sort | uniq",
            ), shell=True, capture_output=True
        )

        # get cleaned list that should be df column names
        stdout = output.stdout.decode().splitlines()
        stdout = [x.replace(';', '').replace('=', '') for x in stdout]

        assert all([x in self.vcf_df.columns.tolist() for x in stdout]), (
            'Not all INFO keys parsed to column names'
        )


    def test_parsed_correct_gnomAD_AF_values(self):
        """
        Test values read into dataframe for gnomAD_AF match the values
        above from the VCF
        """
        # read gnomAD_AF values from vcf
        output = subprocess.run(
            (
                f"grep -v '^#' {self.test_vcf} | grep -oh "
                f"'gnomAD_AF=[0-9\.e\-]*;' | sort | uniq"
            ), shell=True, capture_output=True
        )

        # clean up values
        stdout = output.stdout.decode().splitlines()
        stdout = sorted(list([
            x.replace(';', '').replace('gnomAD_AF=', '') for x in stdout
        ]))

        # get AF values from dataframe
        df_values = sorted(list(self.vcf_df['CSQ_gnomAD_AF'].unique().tolist()))

        assert all([str(x) == str(y) for x, y in zip(stdout, df_values)]), (
            "gnomAD AF values in VCF do not match those in dataframe"
        )


class TestFormatSample():
    """
    Tests for splitColumns.format_fields() that creates new columns from FORMAT
    fields, combining with respective values from SAMPLE column
    """
    # run dataframe through splitColumns.format_fields() to split out FORMAT/SAMPLE
    test_vcf = os.path.join(TEST_DATA_DIR, "NA12878_unittest.split.vcf")

    # run dataframe through splitColumns.info() to split out INFO column
    vcf_df = read_test_vcf(vcf_file=test_vcf)
    vcf_df = splitColumns().split(vcf_df)


    # get list of FORMAT fields from VCF FORMAT column
    output = subprocess.run((
        f"grep -v '^#' {test_vcf} | cut -f9 | sort | uniq"
    ), shell=True, capture_output=True)

    format_fields = sorted(output.stdout.decode().split())[0].split(':')

    # fields already present in df from INFO column will have had suffix added,
    # therefore we will check if they are there to select the correct fields
    for idx, field in enumerate(format_fields):
        if f"{field} (FMT)" in vcf_df.columns:
            format_fields[idx] = f"{field} (FMT)"

    # get all SAMPLE values from vcf
    output = subprocess.run((
        f"grep -v '^#' {test_vcf} | cut -f10"
    ), shell=True, capture_output=True)

    sample_strings_vcf = output.stdout.decode().splitlines()

    # read the sample strings for columns in df, join back together and remove
    # nans from columns that have no values
    sample_strings_df = vcf_df[format_fields].astype(str)
    sample_strings_df = sample_strings_df.agg(':'.join, axis=1).tolist()
    sample_strings_df = [x.replace(':nan', '') for x in sample_strings_df]


    def test_format_sample_values_are_correct(self):
        """
        Tests if the FORMAT / SAMPLE values in dataframe match values in vcf
        """
        assert self.sample_strings_df == self.sample_strings_vcf, (
            "SAMPLE values in dataframe do not match those in test vcf"
        )


if __name__ == "__main__":
    info = TestInfoColumn()
    info.test_parsed_correct_columns_from_info_records()
    info.test_parsed_correct_gnomAD_AF_values()

    format = TestFormatSample()
    format.test_format_sample_values_are_correct()
