"""
Extract by location
"""

import json
import logging
import os
from pathlib import Path
import shutil
import sys
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

LOG_FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=LOG_FORMAT)


def csv_2_geojson(csv_file, latitude, longitude, epsg, output_file_name):
    """
    Convert a CSV to a GeoJSON.

    Parameters
    ----------
    csv_file : str
        CSV file to create vector file.
    latitude : str
        Attribute with latitude coordinates.
    longitude : str
        Attribute with longitude coordinates.
    epsg : integer
        CRS EPSG code of coordinates.
    output_file_name : str
        Name of vector file.

    Returns
    -------
    A vector GeoJSON.

    """
    csv_data = pd.read_csv(csv_file,
                           header=0)
    df = csv_data.copy()
    geometry = [Point(xy) for xy in zip(df[longitude], df[latitude])]
    gdf = gpd.GeoDataFrame(df, crs=epsg, geometry=geometry)
    gdf.to_file(output_file_name, driver='GeoJSON')

def load_inputs(input_path):
    inputs_desc = json.load(open(input_path))
    inputs = inputs_desc.get('inputs')
    parameters = inputs_desc.get('parameters')
    return inputs, parameters


def main():
    WORKING_DIR = os.getenv('DELAIRSTACK_PROCESS_WORKDIR')
    if not WORKING_DIR:
        raise KeyError('DELAIRSTACK_PROCESS_WORKDIR environment variable must be defined')
    WORKING_DIR = Path(WORKING_DIR).resolve()

    logging.debug('Extracting inputs and parameters...')

    # Retrieve inputs and parameters from inputs.json
    inputs, parameters = load_inputs(WORKING_DIR / 'inputs.json')

    # Get info for the inputs
    csv = inputs.get('csv')
    csv_path = inputs['csv']['components'][0]['path']
    logging.info('CSV dataset: {name!r} (id: {id!r})'.format(
        name=csv['name'],
        id=csv['_id']))

    out_filename = parameters.get('output_file_name')
    out_filename_ok = out_filename + '.geojson'
    logging.info('Outfile name: {name!r} '.format(
        name=out_filename_ok))

    latitude = parameters.get('latitude')
    logging.info('Latitude: {name!r} '.format(
        name=latitude))
    
    longitude = parameters.get('longitude')
    logging.info('Longitude: {name!r} '.format(
        name=longitude))
    
    epsg = parameters.get('epsg')
    logging.info('EPSG: {name!r} '.format(
        name=epsg))

    # Create the output vector
    logging.debug('Creating the output vector')
    outpath = WORKING_DIR / out_filename_ok
    logging.info('Output path: {name!r} '.format(
        name=outpath))

    # Create geosjon
    logging.info('Convert CSV to GeoJSON')
    csv_2_geojson(
        csv_file=csv_path,
        latitude=latitude,
        longitude=longitude,
        epsg=epsg,
        output_file_name=outpath)

    # Create the outputs.json to describe the deliverable and its path
    logging.debug('Creating the outputs.json')
    output = {
        "outputs": {
            "output_vector": {  # Must match the name of deliverable in extract_mp.yaml
                "type": "vector",
                "format": "json",
                "name": out_filename,
                "components": [
                    {
                        "name": "vector",
                        "path": str(outpath)
                    }
                ]
            }
        },
        "version": "0.1"
    }
    with open(WORKING_DIR / 'outputs.json', 'w+') as f:
        json.dump(output, f)

    logging.info('End of processing.')


if __name__ == '__main__':
    main()
