#!/usr/bin/env python3
"""
Unit and regression test for data_proc.py
"""
import errno
import os
import sys
import unittest
from contextlib import contextmanager
from io import StringIO
import pandas as pd
import numpy as np
import logging
from otu_proj.data_proc import main, data_process_analysis

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

CURRENT_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(CURRENT_DIR, '..')
TEST_DATA_DIR = os.path.join(CURRENT_DIR, 'data_proc')
PROJ_DIR = os.path.join(MAIN_DIR, 'otu_proj')
DATA_DIR = os.path.join(PROJ_DIR, 'data')
SAMPLE_DATA_FILE_LOC = os.path.join(DATA_DIR, 'OTU_data.xlsx')
SAMPLE_DATA2_FILE_LOC = os.path.join(DATA_DIR, 'OTU_data2.xlsx')
DATA_FNAME = os.path.basename(SAMPLE_DATA_FILE_LOC)
FNAME = os.path.splitext(DATA_FNAME)[0]

# Assumes running tests from the main directory
DEF_XLSX_OUT = os.path.join(MAIN_DIR, 'OTU_data_processed.xlsx')
DEF_PNG_OUT = os.path.join(MAIN_DIR, 'OTU_data.png')


def silent_remove(filename, disable=False):
    """
    Removes the target file name, catching and ignoring errors that indicate that the
    file does not exist.
    @param filename: The file to remove.
    @param disable: boolean to flag if want to disable removal
    """
    if not disable:
        try:
            os.remove(filename)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise


class TestMain(unittest.TestCase):
    # These tests make sure that the program can run properly from main
    def testSampleData(self):
        # Checks that runs with defaults and that files are created
        test_input = ["-d", SAMPLE_DATA_FILE_LOC]
        try:
            if logger.isEnabledFor(logging.DEBUG):
                main(test_input)
            # checks that the expected message is sent to standard out
            with capture_stdout(main, test_input) as output:
                self.assertTrue("OTU_data_processed.xlsx" in output)

            self.assertTrue(os.path.isfile("OTU_data_processed.xlsx"))
            self.assertTrue(os.path.isfile("OTU_data.png"))
        finally:
            silent_remove(DEF_XLSX_OUT, disable=DISABLE_REMOVE)
            silent_remove(DEF_PNG_OUT, disable=DISABLE_REMOVE)


class TestMainFailWell(unittest.TestCase):
    def testMissingFile(self):
        test_input = ["-d", "ghost.xlsx"]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("ghost.xlsx" in output)


class TestDataProcessAnalysis(unittest.TestCase):
    def testSampleData(self):
        # Tests that the mean and standard deviation dataframes generated by the data_process_analysis function
        # match saved expected results
        xlsx_data = pd.read_excel(SAMPLE_DATA_FILE_LOC, index_col=0)
        analysis_mean_vals, analysis_sd_vals = data_process_analysis(xlsx_data, FNAME)
        expected_mean_vals = pd.read_excel(os.path.join(TEST_DATA_DIR, "OTU_data_results.xlsx"),
                                           sheet_name='mean', index_col=0)
        expected_sd_vals = pd.read_excel(os.path.join(TEST_DATA_DIR, "OTU_data_results.xlsx"),
                                         sheet_name='sd', index_col=0)
        self.assertTrue(np.allclose(analysis_mean_vals, expected_mean_vals) and
                        np.allclose(analysis_sd_vals, expected_sd_vals))

    def testSampleData2(self):
        # A second check, with slightly different values, of the data_analysis function
        xlsx_data = pd.read_excel(SAMPLE_DATA2_FILE_LOC, index_col=0)
        analysis_mean_vals, analysis_sd_vals = data_process_analysis(xlsx_data, FNAME)
        expected_mean_vals = pd.read_excel(os.path.join(TEST_DATA_DIR, "OTU_data2_results.xlsx"),
                                           sheet_name='mean', index_col=0)
        expected_sd_vals = pd.read_excel(os.path.join(TEST_DATA_DIR, "OTU_data2_results.xlsx"),
                                         sheet_name='sd', index_col=0)
        self.assertTrue(np.allclose(analysis_mean_vals, expected_mean_vals) and
                        np.allclose(analysis_sd_vals, expected_sd_vals))


# Utility functions

# From http://schinckel.net/2013/04/15/capture-and-test-sys.stdout-sys.stderr-in-unittest.testcase/
@contextmanager
def capture_stdout(command, *args, **kwargs):
    # pycharm doesn't know six very well, so ignore the false warning
    # noinspection PyCallingNonCallable
    out, sys.stdout = sys.stdout, StringIO()
    command(*args, **kwargs)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out


@contextmanager
def capture_stderr(command, *args, **kwargs):
    # pycharm doesn't know six very well, so ignore the false warning
    # noinspection PyCallingNonCallable
    err, sys.stderr = sys.stderr, StringIO()
    command(*args, **kwargs)
    sys.stderr.seek(0)
    yield sys.stderr.read()
    sys.stderr = err