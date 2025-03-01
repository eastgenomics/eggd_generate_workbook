<!-- dx-header -->

# egg_generate_workbook (DNAnexus Platform App)

![pytest](https://github.com/eastgenomics/eggd_generate_variant_workbook/actions/workflows/pytest.yml/badge.svg)

## What does this app do?

Generates an Excel workbook from vcf(s)

## What are typical use cases for this app?

This app may be executed as a standalone app.

## What data are required for this app to run?

**Packages**

* Packages from htslib DNAnexus asset:
  * bcftools
  * bcftools -split-vep plugin
* Python packages (specified in requirements.txt)

**File inputs (required)**:

- `--vcfs`: vcf file(s) to write to Excel workbook sheets

**Other Inputs (optional):**

`--additional_files` (`array:files)`: Additional files to be read in and written to additional sheets, expected to be some form of delimited file (i.e. tsv / csv). This will also accept vcfs, which will have a minimal set of formatting applied for readability (i.e splitting of INFO fields).

`--exclude_columns` (`string`): Columns of VCF to exclude from output workbook.

`--include_columns` (`string`): Columns of VCF to only include in output workbook.

`--reorder_columns` (`string`): Order of fields from VCF in output xlsx columns, any not specified will be appended to end.

`--rename_columns` (`string`): `=` separated key value pairs of VCF fields to rename in output xlsx (e.g. `"gnomADg_AF=gnomAD_genomes_AF"`).

`--filter` (`string`): `bcftools filter` formatted string (see examples below).

`--types` (`string`): `=` separated key value pairs of `{field}={type}` to overwrite in VCF header (i.e `CSQ_gnomADg_AF=Float`). This is required where the field is specified for filtering, but the type is wrongly set in the header. Field types for a given vcf may be inspected with `--print_header`.

`--images` (`array:files`): Image(s) to be written to separate additional sheets, sizes can be set with `--image_sizes` and sheet names with `--image_sheet_names`

`--image_sizes` (`list`): Colon separated `width:height` sizes in pixels for writing images, if specified these MUST be the same number as the number of files passed and in the same order.

`--image_sheet_names` (`list`): Names to use for image file sheets, if specified these MUST be the same number as the number of files passed and in the same order `-iimages=graph1.png -iimages=another_image.jpeg -iimage_sheet_names='myNiceGraph someImage'`). If not given, sheets will be named `image_1, image_2...`.

`--keep_tmp` (`bool`): Determines if to upload the intermediate bcftools split and filtered vcfs. `*.split.vcf.gz` is the output from `bcftools split-vep` and `*.filter.vcf.gz` is the output from `bcftools filter`.

`--keep_filtered` (`bool`): Determines if filtered rows from `--filter` are retained in a seperate 'excluded' tab (default: `True`).

`--add_samplename_column` (`bool`): Determines if to add sample name as first column in each sheet (default: `False`). Column will be named `sampleName`, will be first column unless `--reorder_columns` is specified.

`--add_comment_column` (`bool`): Determines if to append empty 'Comment' column to end of each sheet of variants.

`--add_classification_column` (`bool`): Determines if to append empty 'Classification' column to end of each sheet of variants.

`--sheet_names` (`list`): Names to use for workbook sheets, these MUST be the same number as the number of vcfs passed and in the same order. If not given, and if there is 1 vcf passed the sheet will be named `variants`, else if multiple vcfs are passed the name prefix of the vcf will be used.

`--additional_sheet_names` (`list`): Names to use for additional file sheets, if specified these MUST be the same number as the number of files passed and in the same order (`-iadditional_files=file1 -iadditional_files=file2 -iadditional_sheet_names='name_1 name_2'`). If not given, the first 31 characters of the filename will be used.

`--freeze_columns` (`string`): Column letter and row number of which to 'freeze' (i.e. always keep in view) for sheets of variants, default is to just keep first header row always in view (A2)

`--colour_cells` (`string`): Add conditional colouring of cells for a given column, this should be specified as column:value_range:colour, where colour is a valid hex value or colour name. Multiple conditions may be given in a single `value_range` for the same column and colour values by chaining multiple with either `&` for all or `|` for any condition (n.b. `&` and `|` cannot be used in the same expression). Column names should be given as they appear in the VCF, except for cases where renaming has been specified with `--rename`, in which case the given column name should be used. Example formats:
```
  # single condition
  -icolour_cells "VF:>=0.9:green"

  # both of two conditions
  -icolour_cells "VF:<0.8&>=0.6:orange"

  # either of two conditions
  -icolour_cells "VF:>0.9|<0.1:red"

  # multiple conditions to colour column across multiple ranges and colours
  -icolour_cells "VF:>=0.9:green VF:<0.9&>=0.4:orange VF:>0.4:red"
```

`--output_prefix` (`string`): Prefix for naming output xlsx file. If not given for single file, the VCF prefix will be used. For 2+ input VCFs this must be specified.

`--merge_vcfs` (`bool`): Determines if to merge multiple VCFs to one sheet (default: `False`).

`--summary` (`string`): If to include summary sheet, specify key of assay. Currently supports `dias`, `helios` and `uranus`.

`--human_filter` (`string`): String to add to summary sheet with humanly readable form of the given filter string. No checking is done of this matching the actual filter(s) used.

`--acmg` (`int`): Number of extra sheet(s) to be added to workbook with reporting criteria against ACMG classifications

`--panel` (`string`): Name of panel to display in summary sheet.

`--clinical_indication` (`string`):  Clinical indication to display in summary sheet

`--print_columns` (`bool`): Print column names of all vcfs that will be output to the xlsx and exit. Useful to identify what will be in the output to include/exclude.

`--print_header` (`bool`): Print header of first vcf and exit. Useful for inspecting all fields and types for filtering.

`--additional_columns` (`string`): List of additional columns to add with hyperlinks to external resources. Currently supports the following: decipher, oncokb, cbioportal and pecan. These should be passed as a space separated strings (i.e. -iadditional_columns="oncoKB PeCan cBioPortal"). Details on exact URLs used are given in the table below.

`--split_hgvs` (`bool`): If true, the c. and p. changes in HGVSc and HGVSp will be split out into DNA and Protein columns respectively, without the transcript

`--lock_sheet` (`bool`): If true, all sheets in the variant workbook are locked for dias pipeline except specific cells

`--af_format` (`string`): Presents the allele frequency (AF) as a decimal (0-1) or as a percent (0-100). Default is decimal. Options are `decimal` or `percent`

`--report_text` (`bool`): If true, a report text column will be added that contains the key variant annotation in one cell. The key variants are gene name, consequence, exon number, HGVSc, HGVSp, cosmic annotation, exisiting variation and allele frequency.

`--join_columns` (`string`): Allows user to join two columns from VCF into a new column with a seperator of choice (i.e `--join_columns="Prev_Count=CSQ_Prev_Count_AC,/,CSQ_Prev_Count_NS"` ). The header needs to be added to the include or rename if this is used

**Example**:

```bash
dx run eggd_generate_variant_workbook \
  -ivcfs="file-G70BB1j45jFpjkPJ2ZB10f47" \
  -ifilter="bcftools filter -e 'CSQ_gnomAD_AF>0.02 | CSQ_gnomADg_AF>0.02 | CSQ_Consequence=\"synonymous_variant\"'" \
  -itypes="CSQ_gnomADg_AF=Float" \
  -irename_cols="gnomADg_AF=gnomAD_genomes_AF" \
  -isummary="dias" \
  -iexclude="MLEAF MQRankSum MLEAC" \
```

The above will do the following:

- filter **out** variants with gnomAD exomes or genomes AF above 2%, or a synonymous variant
- set the type for gnomAD genomes AF in the vcf header to `Float` to allow filtering
- rename the gnomAD genomes AF column
- add the summary sheet for Dias
- exclude the `MLEAF`, `MGRankSum` and `MLEAC` columns from the output
- keep the filtered out variants in a separate sheet (default behaviour)


**Notes on inputs**

- `-summary` currently only accepts `dias` as an option, which adds the summary sheet specific for samples processed through the Dias pipeline
- filtering with `-filter` accepts any valid `bcftools` command where the vcf would be passed at the end (i.e. `bcftools filter -e 'CSQ_gnomAD_AF>0.02' sample.vcf`). Commands that are chained with pipes where the vcf is passed to the first command will NOT work (i.e. `bcftools filter -e 'CSQ_gnomAD_AF>0.02' sample.vcf | bcftoools ...`). See the filtering section below for examples.
- `-include_columns` and `-exclude_columns` are mutually exclusive and can not be passed together
- any arguments that are strings and passing multiple should be one space seperated string (i.e. `-iexclude="MLEAF MQRankSum MLEAC"`)
- Fields in `INFO` and `FORMAT` columns will be split to individual columns, with the field key as the column name. If any duplicates are in the **FORMAT** column, these will have the suffix `(FMT)` (i.e. if depth is present in both `INFO` and `FORMAT`, the depth from `INFO` will be in column `DP` and the depth from `FORMAT` will be in `DP (FMT)`).
- If the CombinedVariantOutput.tsv file from Illumina's TSO500 local app is passed to `-iadditional_files`, only the TMB, MSI and Gene Amplifications sections will be written to the sheet.
- If the MetricsOutput.tsv file from Illumina's TSO500 local app is passed to `-iadditional_files`, the given sample's metrics will attempt to be parsed from the file. If the sample prefix inferred from the input vcf prefix can't be parsed from the file, then the whole metrics file will be written to the sheet.


**Filtering**

Filtering of the input vcf(s) is achieved by passing `bcftools` commands to the `-filter` argument. These should be passed without specifying the vcf or `-o` output argument, as these are set in the app. These require passing the exact name of the field as will be in the vcf, any fields coming from the VEP annotation will be prefixed with `CSQ_` (i.e. the `gnomAD_AF` will be `CSQ_gnomAD_AF`). The names and types set can be viewed by passing `-view_header`.

If the type is wrongly set in the vcf header (i.e. AF values set `String`), these will not be valid for filtering. Therefore, if you are specifying these fields for filtering, the `-types` argument must also be passed to specify the correct field type for the given column (i.e. `-itypes="CSQ_gnomADg_AF=Float"`).

Furthermore, the filtering allows for using the logic described in the [bcftools documentation][bcftools]. No checking of what is being filtered is done (other than if bcftools returns a non-zero exit code, in which case an AssertionError will be raised). Therefore, it is up to the user to ensure the bcftools command being passed filters as intended.

Please be aware of the difference between using `-i / --include` and `-e / --exclude`, as they may not filter the same (i.e. including under 2% (`-i 'gnomAD_AF<0.02'`) != excluding over 2% (`-e gnomAD_AF>0.02`)). In this case, missing values (represented in the vcf with a `'.'`) will be filtered **out** with `--include` as they will not meet the filter. If they should be retained, `--exclude` should be used.

If running the filtering with any operator containing `!` (i.e. `CSQ_ClinVar_CLNSIG!~ \"pathogenic\/i\"`) via an interactive shell, `set +H` must first be set to stop shell history substitution, see the GNU set builtin [documentation][set-docs] for details.

**Examples of filters**
```
# filtering gnomAD at 2%
-ifilter="bcftools filter -e 'CSQ_gnomAD_AF>0.02'"

# filtering gnomAD exomes and genomes at 2%
-ifilter="bcftools filter -e 'CSQ_gnomAD_AF>0.02 | CSQ_gnomADg_AF>0.02'"

# filtering out synonymous consequence
-ifilter="bcftools filter -e 'CSQ_Consequence==\"synonymous_variant\"'"

# filter out gnomAD exomes and genomes at 2%, and synonymous/intronic variants EXCEPT if pathogenic in ClinVar (with or without conflicts)
-ifilter="bcftools filter -e '(CSQ_Consequence==\"synonymous_variant\" | CSQ_Consequence==\"intron_variant\" | CSQ_gnomADe_AF>0.02 | CSQ_gnomADg_AF>0.02) & CSQ_ClinVar_CLNSIG!~ \"pathogenic\/i\" & CSQ_ClinVar_CLNSIGCONF!~ \"pathogenic\/i\"'"

```

Useful resources:

- [bcftools expressions][bcftools-expressions]


## Hyperlinks in output Excel file

Some columns will be formatted with URLs as hyperlinks in the output variant sheets, this is dependent on the INFO field names from the VCF. Currently, the following INFO fields (case insensitive, either exact match or contains given name) and URLs are used:

| INFO field | URL |
|---         | --- |
| gnomad (contains) | https://gnomad.broadinstitute.org/variant/ |
| existing_variation (exact) | https://www.ncbi.nlm.nih.gov/snp/ |
| clinvar (exact) | https://www.ncbi.nlm.nih.gov/clinvar/variation/ |
| cosmic (exact) | https://cancer.sanger.ac.uk/cosmic/search?q= |
| hgmd (exact) | https://my.qiagendigitalinsights.com/bbp/view/hgmd/pro/mut.php?acc= |
| mastermind_mmid3 (exact) | https://mastermind.genomenon.com/detail?mutation= |

URLs used for generating of columns specified from `-iadditional_columns`:

| Name | URL |
| ---  | --- |
| decipher | https://www.deciphergenomics.org/sequence-variant/CHROM-POS-REF-ALT |
| oncoKB | https://www.oncokb.org/gene/ |
| PeCan | https://pecan.stjude.cloud/variants/proteinpaint/?gene=SYMBOL |
| cBioPortal | https://www.cbioportal.org/results/mutations?case_set_id=all&gene_list=SYMBOL&cancer_study_list=5c8a7d55e4b046111fee2296 |

n.b. the above link to cBioPortal defaults to the 'TCGA PanCancer Atlas Studies' dataset.


## What does this app output?

This app outputs an Excel workbook and (optionally) the intermediate .split.vcf.gz output from calling bcftools +split-vep and .filter.vcf.gz which has the EXCLUDE filter tag added to the FILTER field for variants filtered out by the provided bcftools command.

This is the source code for an app that runs on the DNAnexus Platform.
For more information about how to run or modify it, see
https://documentation.dnanexus.com/.


## File details
The app will also add `details` metadata, in terms of variant counts, to the output xlsx report DNAnexus file. Example file details if `-isummary=Dias`, `-iclinical_indication=R208.1_Inherited breast cancer and ovarian cancer_P` and an `-ifilter` is provided, with `-ikeep_filtered=True`:
```
  "clinical_indication": "R208.1_Inherited breast cancer and ovarian cancer_P",
  "included": 10,
  "excluded": 255
```
Note: if `-isummary` not Dias, if `-ikeep_filtered=False`, and if `-iclinical_indication` not provided then the only details added to the file would be `"included": 10`. In this case, if no filtering is performed either then only `"variants": 265` would be added as details.

#### This app was made by EMEE GLH

[bcftools]: https://samtools.github.io/bcftools/bcftools.html#filter
[bcftools-expressions]: https://samtools.github.io/bcftools/bcftools.html#expressions
[set-docs]: https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html

