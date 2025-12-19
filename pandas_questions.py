"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    referendum = pd.read_csv(
        'data/referendum.csv', sep=';', dtype={'Department code': str}
    )
    regions = pd.read_csv('data/regions.csv', dtype={'code': str})
    departments = pd.read_csv(
        'data/departments.csv',
        dtype={'code': str, 'region_code': str}
    )

    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """

    regions_df = regions[['code', 'name']].copy()
    regions_df['code'] = regions_df['code'].astype(str).str.zfill(2)
    regions_df = regions_df.rename(columns={'code': 'code_reg',
                                            'name': 'name_reg'})

    departments_df = departments[['code', 'name', 'region_code']].copy()
    departments_df['code'] = departments_df['code'].astype(str).str.zfill(2)
    departments_df['region_code'] = departments_df['region_code'].astype(str)
    numeric_region_codes = departments_df['region_code'].str.isdigit()
    departments_df.loc[numeric_region_codes, 'region_code'] = (
        departments_df.loc[numeric_region_codes, 'region_code'].str.zfill(2)
    )
    departments_df = departments_df.rename(
        columns={'code': 'code_dep', 'name': 'name_dep'}
    )

    merged = departments_df.merge(
        regions_df, left_on='region_code', right_on='code_reg',
        how='left', validate='many_to_one'
    )

    return merged[['code_reg', 'name_reg', 'code_dep', 'name_dep']]


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum data with territorial info, excluding overseas areas."""

    referendum_df = referendum.copy()
    referendum_df['Department code'] = (
        referendum_df['Department code'].astype(str).str.zfill(2)
    )
    french_abroad_mask = referendum_df['Department code'].str.contains(
        'Z', na=False
    )
    referendum_df = referendum_df.loc[~french_abroad_mask]

    merged = referendum_df.merge(
        regions_and_departments,
        left_on='Department code',
        right_on='code_dep',
        how='inner',
        validate='many_to_one'
    )
    dom_tom_com_mask = merged['code_dep'].str.len() > 2

    return merged.loc[~dom_tom_com_mask].reset_index(drop=True)


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region."""

    vote_columns = [
        'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B'
    ]
    grouped = (
        referendum_and_areas
        .groupby(['code_reg', 'name_reg'], sort=False)[vote_columns]
        .sum()
        .reset_index()
    )
    ordered_columns = ['name_reg'] + vote_columns

    return grouped.set_index('code_reg')[ordered_columns]


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use the method `GeoDataFrame.plot` to display the result map. The results
      should display the rate of 'Choice A' over all expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """

    gdf_regions = gpd.read_file('data/regions.geojson')
    gdf_regions['code'] = gdf_regions['code'].astype(str).str.zfill(2)

    referendum_regions = referendum_result_by_regions.reset_index()
    merged = gdf_regions.merge(
        referendum_regions,
        left_on='code',
        right_on='code_reg',
        how='left'
    )
    expressed = merged['Choice A'] + merged['Choice B']
    merged['ratio'] = merged['Choice A'] / expressed
    merged.loc[expressed == 0, 'ratio'] = pd.NA
    merged.plot(column='ratio', legend=True, cmap='RdYlBu_r')

    return merged


if __name__ == "__main__":

    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(
        df_reg, df_dep
    )
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    plot_referendum_map(referendum_results)
    plt.show()
