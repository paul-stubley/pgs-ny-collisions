import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon
import plotly.express as px

def return_figures():
    """Creates plotly visualizations

    Args:
        None

    Returns:
        list (dict): list containing the four plotly visualizations

    """

    # Read in data
    collisions = gpd.read_file("data/nypd-motor-vehicle-collisions_head.csv")
    hospitals  = gpd.read_file("data/hospitals/hospitals.shp")

    # Remove rows with unknown Lat or Long
    collisions = collisions[collisions.LATITUDE !=""]
    collisions = collisions[collisions.LONGITUDE!=""]
    collisions.rename(columns={'LATITUDE':'latitude','LONGITUDE':'longitude'}, inplace=True)

    # Create geometry column
    collisions.geometry = gpd.points_from_xy(collisions.longitude.astype(float), collisions.latitude.astype(float))
    collisions.crs = {'init': 'epsg:4326'}    # Plain lat/long is 4326
    collisions = collisions.to_crs(epsg=2263) # Move to the CRS of the hosital data (geometry column changes, lat/long don't)

    # Fill hospital null capacities with median capacity
    hospitals = hospitals.fillna(hospitals.capacity.median())
    hospitals.capacity = hospitals.capacity.astype(float)
    hospitals.name     = hospitals.name.str.title() # Change case of name column

    # Calculate 10km coverage
    coverage = pd.DataFrame(hospitals.geometry.buffer(10000), columns = ['buffer'])
    near_hospitals = hospitals.geometry.buffer(10000).unary_union
    outside_range = collisions[~collisions.geometry.apply(lambda x: near_hospitals.contains(x))]

    fig_collisions = px.density_mapbox(collisions
                            , lat='latitude'
                            , lon='longitude'
                            , radius=8
                            , center=dict(lat=40.71, lon=-74)
                            , zoom=8.9
                            , mapbox_style="open-street-map"
                            #, range_color=(0,5) 
                            , height=600
                          )

    fig_hospitals = px.scatter_mapbox(hospitals
                            , lat='latitude'
                            , lon='longitude'
                            , size='capacity'
                            , center=dict(lat=40.71, lon=-74)
                            , zoom=8.9
                            , text='name'
                            , color = 'capacity'
                            , mapbox_style="open-street-map"
                            , color_continuous_scale='Bluered_r'
                            , opacity = .9
                            , height=600
                            )

    fig_hospitals_uncoloured = px.scatter_mapbox(hospitals
                            , lat='latitude'
                            , lon='longitude'
                            , size='capacity'
                            , text='name'
                            , center=dict(lat=40.71, lon=-74)
                            , zoom=8.9
                            , mapbox_style="open-street-map"
                            , opacity = .9
                            , height=600
                            )

    fig_uncovered = px.density_mapbox(outside_range
                            , lat='latitude'
                            , lon='longitude'
                            , radius=8
                            , center=dict(lat=40.71, lon=-74)
                            , zoom=8.9
                            , mapbox_style="open-street-map"
                            #, range_color=(0,5)
                            , height=600)

    fig_uncovered.add_trace(fig_hospitals_uncoloured.data[0])

    layout_fig_collisions = dict(title = 'Vehicle Collisions')
    layout_fig_hospitals  = dict(title = 'Hospital Capacities')
    layout_fig_uncovered  = dict(title = 'Collisions more than 10km from the nearest hospital')

    # append all charts to the figures list
    figures = []
    figures.append(dict(data=fig_collisions, layout=layout_fig_collisions))
    figures.append(dict(data=fig_hospitals, layout=layout_fig_hospitals))
    figures.append(dict(data=fig_uncovered, layout=layout_fig_uncovered))
    return figures