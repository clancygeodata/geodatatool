"""Main module."""

import csv
import os
import ee
import ipyleaflet
from ipyleaflet import FullScreenControl, LayersControl, DrawControl, MeasureControl, ScaleControl, TileLayer
from .common import ee_initialize, tool_template
from .toolbar import main_toolbar

class Map(ipyleaflet.Map):
    """This map class inherits the ipyleaflet Map class.

    Args:
        ipyleaflet (ipyleaflet.Map): An ipyleaflet map.
    """    

    def __init__(self, **kwargs):

        if "center" not in kwargs:
            kwargs["center"] = [40, -100]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 4

        if "scroll_wheel_zoom" not in kwargs:
            kwargs["scroll_wheel_zoom"] = True

        super().__init__(**kwargs)

        if "height" not in kwargs:
            self.layout.height = "600px"
        else:
            self.layout.height = kwargs["height"]

        self.add_control(FullScreenControl())
        self.add_control(LayersControl(position="topright"))
        self.add_control(DrawControl(position="topleft"))
        self.add_control(MeasureControl())
        self.add_control(ScaleControl(position="bottomleft"))

        main_toolbar(self)

        if "google_map" not in kwargs:
            layer = TileLayer(
                url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                attribution="Google",
                name="Google Maps",
            )
            self.add_layer(layer)
        else:
            if kwargs["google_map"] == "ROADMAP":
                layer = TileLayer(
                    url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                    attribution="Google",
                    name="Google Maps",
                )
                self.add_layer(layer)
            elif kwargs["google_map"] == "HYBRID":
                layer = TileLayer(
                    url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                    attribution="Google",
                    name="Google Satellite"
                )
                self.add_layer(layer)


    def add_geojson(self, in_geojson, style=None, layer_name="Untitled"):
        """Adds a GeoJSON file to the map.

        Args:
            in_geojson (str): The file path to the input GeoJSON file.
            style (dict, optional): The style for visualizing the GeoJSON. Defaults to None.
            layer_name (str, optional): The layer name for the GeoJSON layer. Defaults to "Untitled".
        
        Raises:
            FileNotFoundError: If the provided file path does not exist.
            TypeError: If the input geojson is not a str or dict.
        """        

        import json

        if isinstance(in_geojson, str):

            if not os.path.exists(in_geojson):
                raise FileNotFoundError("The provided GeoJSON file could not be found.")

            with open(in_geojson) as f:
                data = json.load(f)
        
        elif isinstance(in_geojson, dict):
            data = in_geojson
        
        else:
            raise TypeError("The input geojson must be a type of str or dict.")

        if style is None:
            style = {
                "stroke": True,
                "color": "#000000",
                "weight": 2,
                "opacity": 1,
                "fill": True,
                "fillColor": "#000000",
                "fillOpacity": 0.4,
            }

        geo_json = ipyleaflet.GeoJSON(data=data, style=style, name=layer_name)
        self.add_layer(geo_json)

    def add_shapefile(self, in_shp, style=None, layer_name="Untitled"):
        """Adds a shapefile layer to the map.

        Args:
            in_shp (str): The file path to the input shapefile.
            style (dict, optional): The style for visualizing the shapefile. Defaults to None.
            layer_name (str, optional): The layer name for the shapefile layer. Defaults to "Untitled".
        """

        geojson = shp_to_geojson(in_shp)
        self.add_geojson(geojson, style=style, layer_name=layer_name)

    def add_ee_layer(
        self, ee_object, vis_params={}, name=None, shown=True, opacity=1.0
    ):
        """Adds a given EE object to the map as a layer.

        Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to {}.
            name (str, optional): The name of the layer. Defaults to 'Layer N'.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """

        ee_layer = ee_tile_layer(ee_object, vis_params, name, shown, opacity)
        self.add_layer(ee_layer)

    addLayer = add_ee_layer

    def add_cluster_from_csv(self, in_csv, latitude="longitude", longitude="latitude", layer_name="Marker cluster"):
        """[summary]

        Args:
            in_csv (str): The input csv file containing longitude and latitude columns.
            latitude (str, optional): The column name of the latitude column. Defaults to 'latitude'.
            longitude (str, optional): The column name of the longitude column. Defaults to 'longitude'.
            layer_name (str, optional): The layer name for the shapefile layer. Defaults to "Marker cluster".
        """        

        from ipyleaflet import GeoJSON, Marker, MarkerCluster

        out_json = in_csv.replace(".csv", ".json")
        
        json_from_csv = csv_to_json(in_csv=in_csv, out_json=out_json, latitude=latitude, longitude=longitude)

        file_path = os.path.abspath(json_from_csv)

        with open(file_path) as f:
            json_data = json.load(f)

        marker_cluster = MarkerCluster(
            markers=[Marker(location=feature['geometry']['coordinates'][::-1]) for feature in json_data['features']],
            name = 'Markers')

        self.add_layer(marker_cluster)

        




def shp_to_geojson(in_shp, out_geojson=None):
    """Converts a shapefile to GeoJSON.

    Args:
        in_shp (str): The file path to the input shapefile.
        out_geojson (str, optional): The file path to the output GeoJSON. Defaults to None.
    
    Raises:
        FileNotFoundError: If the input shapefile does not exist.
    
    Returns:
        dict: The dictionary of the GeoJSON.
    """
    
    import json
    import shapefile

    in_shp = os.path.abspath(in_shp)

    if not os.path.exists(in_shp):
        raise FileNotFoundError("The provided shapefile could not be found.")

    sf = shapefile.Reader(in_shp)
    geojson = sf.__geo_interface__

    if out_geojson is None:
        return geojson
    else:
        out_geojson = os.path.abspath(out_geojson)
        out_dir = os.path.dirname(out_geojson)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        with open(out_geojson, "w") as f:
            f.write(json.dumps(geojson))


def ee_tile_layer(
    ee_object, vis_params={}, name="Layer untitled", shown=True, opacity=1.0
):
    """Converts an Earth Engine layer to ipyleaflet TileLayer.
    
    Args:
        ee_object (Collection|Feature|Image|MapId): The object to add to the map.
        vis_params (dict, optional): The visualization parameters. Defaults to {}.
        name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
        shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.

    Raises:
        AttributeError: If the object from Earth Engine is not ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection.

    Returns:
        object: An ipyleaflet TileLayer visualizing the Earth Engine object.
    """

    image = None

    if (
        not isinstance(ee_object, ee.Image)
        and not isinstance(ee_object, ee.ImageCollection)
        and not isinstance(ee_object, ee.FeatureCollection)
        and not isinstance(ee_object, ee.Feature)
        and not isinstance(ee_object, ee.Geometry)
    ):
        err_str = "\n\nThe ee_object argument must be an instance of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
        raise AttributeError(err_str)

    if (
        isinstance(ee_object, ee.geometry.Geometry)
        or isinstance(ee_object, ee.feature.Feature)
        or isinstance(ee_object, ee.featurecollection.FeatureCollection)
    ):
        features = ee.FeatureCollection(ee_object)

        width = 2

        if "width" in vis_params:
            width = vis_params["width"]

        color = "000000"

        if "color" in vis_params:
            color = vis_params["color"]

        image_fill = features.style(**{"fillColor": color}).updateMask(
            ee.Image.constant(0.5)
        )
        image_outline = features.style(
            **{"color": color, "fillColor": "00000000", "width": width}
        )

        image = image_fill.blend(image_outline)

    elif isinstance(ee_object, ee.image.Image):
        image = ee_object

    elif isinstance(ee_object, ee.imagecollection.ImageCollection):
        image = ee_object.mosaic()

    map_id_dict = ee.Image(image).getMapId(vis_params)
    tile_layer = TileLayer(
        url=map_id_dict["tile_fetcher"].url_format,
        attribution="Google Earth Engine",
        name=name,
        opacity=opacity,
        visible=shown,
    )
    return tile_layer

def csv_to_shp(in_csv, out_shp, latitude="latitude", longitude="longitude"):
    """Converts a csv file with latlon info to a point shapefile.
    Args:
        in_csv (str): The input csv file containing longitude and latitude columns.
        out_shp (str): The file path to the output shapefile.
        latitude (str, optional): The column name of the latitude column. Defaults to 'latitude'.
        longitude (str, optional): The column name of the longitude column. Defaults to 'longitude'.
    """
    import shapefile as shp

    if in_csv.startswith("http") and in_csv.endswith(".csv"):
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        out_name = os.path.basename(in_csv)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        download_from_url(in_csv, out_dir=out_dir)
        in_csv = os.path.join(out_dir, out_name)

    out_dir = os.path.dirname(out_shp)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        points = shp.Writer(out_shp, shapeType=shp.POINT)
        with open(in_csv, encoding="utf-8") as csvfile:
            csvreader = csv.DictReader(csvfile)
            header = csvreader.fieldnames
            [points.field(field) for field in header]
            for row in csvreader:
                points.point((float(row[longitude])), (float(row[latitude])))
                points.record(*tuple([row[f] for f in header]))

        out_prj = out_shp.replace(".shp", ".prj")
        with open(out_prj, "w") as f:
            prj_str = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]] '
            f.write(prj_str)

    except Exception as e:
        print(e)

def csv_to_json(in_csv, out_json, latitude="latitude", longitude="longitude"):
    """Converts a csv file with latlon info to a point shapefile.
    Args:
        in_csv (str): The input csv file containing longitude and latitude columns.
        out_shp (str): The file path to the output shapefile.
        latitude (str, optional): The column name of the latitude column. Defaults to 'latitude'.
        longitude (str, optional): The column name of the longitude column. Defaults to 'longitude'.
    """
    in_shp = csv_to_shp(in_csv=in_csv, out_json=out_json, latitude=latitude, longitude=longitude)

    geojson = shp_to_geojson(in_shp)
    
    out_json = geojson

    return out_json