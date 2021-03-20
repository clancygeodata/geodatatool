"""Module for adding visual media in Jupyter Notebook."""

def load_image_from_url(url):
    """Loads an image from the specified URL.
    Args:
        url (str): URL of the image.
    Returns:
        object: Image object.
    """
    from PIL import Image
    import requests
    from io import BytesIO

    # from urllib.parse import urlparse

    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        print(e)

def display_youtube(id="h0pz3S6Tvx0"):
    """Displays a YouTube video within Jupyter notebooks.
    Args:
        id (str, optional): Unique ID of the video. Defaults to 'h0pz3S6Tvx0'.
    """
    from IPython.display import YouTubeVideo, display
    import ipywidgets

    if "/" in id:
        id = id.split("/")[-1]

    try:
        out = ipywidgets.Output(layout={"width": "815px"})
        # layout={'border': '1px solid black', 'width': '815px'})
        out.clear_output(wait=True)
        display(out)
        with out:
            display(YouTubeVideo(id, width=800, height=450))
    except Exception as e:
        print(e)