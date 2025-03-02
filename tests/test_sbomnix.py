#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022-2023 Technology Innovation Institute (TII)
#
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=invalid-name

""" Tests for sbomnix """

import os
import subprocess
import shutil
from pathlib import Path
import json
import imghdr
import pandas as pd
import jsonschema
import pytest

MYDIR = Path(os.path.dirname(os.path.realpath(__file__)))
TEST_WORK_DIR = MYDIR / "sbomnix_test_data"
TEST_NIX_RESULT = TEST_WORK_DIR / "result"
SBOMNIX = MYDIR / ".." / "sbomnix" / "main.py"
NIXGRAPH = MYDIR / ".." / "nixgraph" / "main.py"
COMPARE_DEPS = MYDIR / "compare_deps.py"
COMPARE_SBOMS = MYDIR / "compare_sboms.py"


################################################################################


@pytest.fixture(autouse=True)
def set_up_test_data():
    """Fixture to set up the test data"""
    print("setup")
    shutil.rmtree(TEST_WORK_DIR, ignore_errors=True)
    TEST_WORK_DIR.mkdir(parents=True, exist_ok=True)
    # Build nixpkgs.hello, output symlink to TEST_NIX_RESULT
    # (assumes nix-build is available in $PATH)
    cmd = ["nix-build", "<nixpkgs>", "-A", "hello", "-o", TEST_NIX_RESULT]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert Path(TEST_NIX_RESULT).exists()
    os.chdir(TEST_WORK_DIR)
    yield "resource"
    print("clean up")
    shutil.rmtree(TEST_WORK_DIR)


def test_sbomnix_help():
    """
    Test sbomnix command line argument: '-h'
    """
    cmd = [SBOMNIX, "-h"]
    assert subprocess.run(cmd, check=True).returncode == 0


def test_sbomnix_cdx_type_runtime():
    """
    Test sbomnix '--type=runtime' generates valid CycloneDX json
    """

    out_path_cdx = TEST_WORK_DIR / "sbom_cdx_test.json"
    cmd = [
        SBOMNIX,
        TEST_NIX_RESULT,
        "--cdx",
        out_path_cdx.as_posix(),
        "--type",
        "runtime",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert out_path_cdx.exists()
    schema_path = MYDIR / "resources" / "cdx_bom-1.3.schema.json"
    assert schema_path.exists()
    validate_json(out_path_cdx.as_posix(), schema_path)


def test_sbomnix_cdx_type_buildtime():
    """
    Test sbomnix '--type=runtime' generates valid CycloneDX json
    """

    out_path_cdx = TEST_WORK_DIR / "sbom_cdx_test.json"
    cmd = [
        SBOMNIX,
        TEST_NIX_RESULT,
        "--cdx",
        out_path_cdx.as_posix(),
        "--type",
        "buildtime",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert out_path_cdx.exists()
    schema_path = MYDIR / "resources" / "cdx_bom-1.3.schema.json"
    assert schema_path.exists()
    validate_json(out_path_cdx.as_posix(), schema_path)


def test_sbomnix_cdx_type_both():
    """
    Test sbomnix '--type=both' generates valid CycloneDX json
    """

    out_path_cdx = TEST_WORK_DIR / "sbom_cdx_test.json"
    cmd = [
        SBOMNIX,
        TEST_NIX_RESULT,
        "--cdx",
        out_path_cdx.as_posix(),
        "--type",
        "both",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert out_path_cdx.exists()
    schema_path = MYDIR / "resources" / "cdx_bom-1.3.schema.json"
    assert schema_path.exists()
    validate_json(out_path_cdx.as_posix(), schema_path)


################################################################################


def test_nixgraph_help():
    """
    Test nixgraph command line argument: '-h'
    """
    cmd = [NIXGRAPH, "-h"]
    assert subprocess.run(cmd, check=True).returncode == 0


def test_nixgraph_png():
    """
    Test nixgraph with png output generates valid png image
    """
    png_out = TEST_WORK_DIR / "graph.png"
    cmd = [NIXGRAPH, TEST_NIX_RESULT, "--out", png_out, "--depth", "3"]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert Path(png_out).exists()
    # Check the output is valid png file
    assert imghdr.what(png_out) == "png"


def test_nixgraph_csv():
    """
    Test nixgraph with csv output generates valid csv
    """
    csv_out = TEST_WORK_DIR / "graph.csv"
    cmd = [NIXGRAPH, TEST_NIX_RESULT, "--out", csv_out, "--depth", "3"]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert Path(csv_out).exists()
    # Check the output is valid csv file
    df_out = pd.read_csv(csv_out)
    assert not df_out.empty


def test_nixgraph_csv_buildtime():
    """
    Test nixgraph with buildtime csv output generates valid csv
    """
    csv_out = TEST_WORK_DIR / "graph_buildtime.csv"
    cmd = [NIXGRAPH, TEST_NIX_RESULT, "--out", csv_out, "--buildtime"]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert Path(csv_out).exists()
    # Check the output is valid csv file
    df_out = pd.read_csv(csv_out)
    assert not df_out.empty


def test_nixgraph_csv_graph_inverse():
    """
    Test nixgraph with '--inverse' argument
    """
    csv_out = TEST_WORK_DIR / "graph.csv"
    cmd = [
        NIXGRAPH,
        TEST_NIX_RESULT,
        "--out",
        csv_out,
        "--depth=100",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert Path(csv_out).exists()
    df_out = pd.read_csv(csv_out)
    assert not df_out.empty

    csv_out_inv = TEST_WORK_DIR / "graph_inverse.csv"
    cmd = [
        NIXGRAPH,
        TEST_NIX_RESULT,
        "--out",
        csv_out_inv,
        "--depth=100",
        "--inverse=libunistring",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert Path(csv_out_inv).exists()
    df_out_inv = pd.read_csv(csv_out_inv)
    assert not df_out_inv.empty

    # When 'depth' covers the entire graph, the output from
    # the two above commands should be the same, except for column
    # 'graph_depth': below, we remove that column from both outputs and
    # compare the two dataframes

    df_out = df_out.drop("graph_depth", axis=1)
    df_out = df_out.sort_values(by=["src_path"])

    df_out_inv = df_out_inv.drop("graph_depth", axis=1)
    df_out_inv = df_out_inv.sort_values(by=["src_path"])

    df_diff = df_difference(df_out, df_out_inv)
    assert df_diff.empty, df_to_string(df_diff)


################################################################################


def test_compare_deps_runtime():
    """
    Compare nixgraph vs sbom runtime dependencies
    """
    graph_csv_out = TEST_WORK_DIR / "graph.csv"
    cmd = [
        NIXGRAPH,
        TEST_NIX_RESULT,
        "--out",
        graph_csv_out,
        "--depth=100",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert Path(graph_csv_out).exists()

    out_path_cdx = TEST_WORK_DIR / "sbom_cdx_test.json"
    cmd = [
        SBOMNIX,
        TEST_NIX_RESULT,
        "--cdx",
        out_path_cdx.as_posix(),
        "--type",
        "runtime",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert out_path_cdx.exists()

    cmd = [
        COMPARE_DEPS,
        "--sbom",
        out_path_cdx,
        "--graph",
        graph_csv_out,
    ]
    assert subprocess.run(cmd, check=True).returncode == 0


def test_compare_deps_buildtime():
    """
    Compare nixgraph vs sbom buildtime dependencies
    """
    graph_csv_out = TEST_WORK_DIR / "graph.csv"
    cmd = [
        NIXGRAPH,
        TEST_NIX_RESULT,
        "--out",
        graph_csv_out,
        "--depth=100",
        "--buildtime",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert Path(graph_csv_out).exists()

    out_path_cdx = TEST_WORK_DIR / "sbom_cdx_test.json"
    cmd = [
        SBOMNIX,
        TEST_NIX_RESULT,
        "--cdx",
        out_path_cdx.as_posix(),
        "--type",
        "buildtime",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert out_path_cdx.exists()

    cmd = [
        COMPARE_DEPS,
        "--sbom",
        out_path_cdx,
        "--graph",
        graph_csv_out,
    ]
    assert subprocess.run(cmd, check=True).returncode == 0


def test_compare_sboms():
    """
    Compare two sbomnix runs with same target produce the same sbom
    """
    out_path_cdx_1 = TEST_WORK_DIR / "sbom_cdx_test_1.json"
    cmd = [
        SBOMNIX,
        TEST_NIX_RESULT,
        "--cdx",
        out_path_cdx_1.as_posix(),
        "--type",
        "buildtime",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert out_path_cdx_1.exists()

    out_path_cdx_2 = TEST_WORK_DIR / "sbom_cdx_test_2.json"
    cmd = [
        SBOMNIX,
        TEST_NIX_RESULT,
        "--cdx",
        out_path_cdx_2.as_posix(),
        "--type",
        "buildtime",
    ]
    assert subprocess.run(cmd, check=True).returncode == 0
    assert out_path_cdx_2.exists()

    cmd = [
        COMPARE_SBOMS,
        out_path_cdx_1,
        out_path_cdx_2,
    ]
    assert subprocess.run(cmd, check=True).returncode == 0


################################################################################


def validate_json(file_path, schema_path):
    """Validate json file matches schema"""
    with open(file_path, encoding="utf-8") as json_file, open(
        schema_path, encoding="utf-8"
    ) as schema_file:
        json_obj = json.load(json_file)
        schema_obj = json.load(schema_file)
        jsonschema.validate(json_obj, schema_obj)


def df_to_string(df):
    """Convert dataframe to string"""
    return (
        "\n"
        + df.to_string(max_rows=None, max_cols=None, index=False, justify="left")
        + "\n"
    )


def df_difference(df_left, df_right):
    """Return dataframe that represents diff of two dataframes"""
    df_right = df_right.astype(df_left.dtypes.to_dict())
    df = df_left.merge(
        df_right,
        how="outer",
        indicator=True,
    )
    # Keep only the rows that differ (that are not in both)
    df = df[df["_merge"] != "both"]
    # Rename 'left_only' and 'right_only' values in '_merge' column
    df["_merge"] = df["_merge"].replace(["left_only"], "EXPECTED ==>  ")
    df["_merge"] = df["_merge"].replace(["right_only"], "RESULT ==>  ")
    # Re-order columns: last column ('_merge') becomes first
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]
    # Rename '_merge' column to empty string
    df = df.rename(columns={"_merge": ""})
    return df


################################################################################


if __name__ == "__main__":
    pytest.main([__file__])


################################################################################
