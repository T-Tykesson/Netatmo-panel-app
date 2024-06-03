import folium
import jinja2
from jinja2 import Template

import panel as pn
import datetime
import logging
import numpy as np
import os
from bokeh.models import Div
from backend_handler import UserInputData, run_program
from back_end.api_counter import (InternalServerError,
                                  NetatmoGeneralError, NoActiveTokenError,
                                  NoApiCallsLeftError, InvalidInputError)
from bokeh.models import ColumnDataSource, WheelZoomTool
from bokeh.plotting import figure
from bokeh.tile_providers import get_provider, Vendors
from bokeh.models import ImageURL
import math
import base64
# Set the Panel extension
pn.extension('mathjax')

image_path = "images/icon.svg"
with open(image_path, "rb") as f:
    svg_data = f.read()
encoded_svg = base64.b64encode(svg_data).decode("utf-8")
svg_url = f"data:image/svg+xml;base64,{encoded_svg}"

def wgs84_to_web_mercator(lon, lat):
    k = 6378137
    x = lon * (k * math.pi / 180.0)
    y = math.log(math.tan((90 + lat) * math.pi / 360.0)) * k
    return x, y

def web_mercator_to_wgs84(x, y):
    k = 6378137
    lon = (x / k) * (180.0 / math.pi)
    lat = (y / k) * (180.0 / math.pi)
    lat = (2 * math.atan(math.exp(lat * (math.pi / 180.0))) - (math.pi / 2.0)) * (180.0 / math.pi)
    return lon, lat

# Add interaction
def update_plot(event):
    x, y = event.x, event.y
    source.data = dict(x=[x], y=[y])
    #image_source.data = dict(url=[url], x=[x], y=[y])
    lon, lat = web_mercator_to_wgs84(x, y)
    latitude_input.value = str(lat)
    longitude_input.value = str(lon)
    #print(f"Clicked location: {lon}, {lat}")

def load_display(x):
    if x == 'on':
        loading.value = True
        loading.visible = True
        loading.name = "Hämtar stationer..."
    if x == 'off':
        loading.value = False
        loading.visible = False
        loading.name = ""
# Define the submit button and its callback

def show_modal(event):
    info_box = pn.pane.Markdown(markdown_text)
    ui.modal[0].clear()
    ui.modal[0].append(info_box)
    ui.open_modal()

def submit(event):
    error_message = ""
    load_display("on")
    try:
        error_div.text = ""
        auth_token = auth_input.value
        start_date = start_date_input.value.strftime('%Y-%m-%d')
        end_date = end_date_input.value.strftime('%Y-%m-%d')
        latitude = float(latitude_input.value)
        longitude = float(longitude_input.value)
        amount = int(amount_input.value)
        time_resolution = time_input.value

        print("auth_token=", auth_token,
              "latitude=", latitude,
              "longitude=", longitude,
              "date_begin=", start_date,
              "date_end=", end_date,
              "scale=", time_resolution,
              "station_amount=", amount)

        # Create UserInputData instance
        input_data = UserInputData(
            auth_token=auth_token,
            latitude=latitude,
            longitude=longitude,
            date_begin=start_date,
            date_end=end_date,
            scale=time_resolution,
            station_amount=amount,
            path=''
        )

    except (KeyError, ValueError) as e:
        error_message = f"Felaktig input, dubbelkolla att alla fält är rätt inskrivna"
        print(e)
        error_div.text = f'<div style="color:red; border: 1px solid red; padding: 5px;">{error_message}</div>'
        load_display("off")
        return

    try:
        # Run the backend function
        output_file = run_program(input_data)

        file_download_button.file = output_file
        file_download_button.filename = os.path.basename(output_file)
        file_download_button.visible = True
    except KeyError as e:
        error_message = f"KeyError <br> {e}"
        print(error_message)

    except ValueError as e:
        error_message = f"Ospecificerat fel <br> Felmeddelande: {e}"
        print(e)

    except InternalServerError as e:
        error_message = "Internfel i Netatmos server, försök igen"
        print(error_message)

    except NetatmoGeneralError as e:
        error_message = f"Ospecificerat netatmofel: {e}"
        print(error_message)
        print(e)

    except NoActiveTokenError as e:
        error_message = "Tokennyckeln är felaktig eller har gått ut, se till att nyckeln stämmer eller hämta en ny"
        print(error_message)

    except NoApiCallsLeftError as e:
        error_message = "Antal förfrågningar till servern har överskridits, för att forstätta skaffa en ny tokennyckel från en annan app på Netatmo"
        print(error_message)

    except InvalidInputError as e:
        error_message = f"Felaktig input: {e}"
        print(str(e))
        
    except Exception as e:
        error_message = f"Ospecificerat fel <br> Felmeddelande: {e}"
        print(e)
    
    if error_message:
        load_display("off")
        error_div.text = f'<div style="color:red; border: 1px solid red; padding: 5px;">{error_message}</div>'
    else:
        error_div.text = ""
        load_display("off")
# Center the map around the specified coordinates
center_lon, center_lat = 11.974559999999997, 57.70887
x_center, y_center = wgs84_to_web_mercator(center_lon, center_lat)

# Create a Bokeh plot
p = figure(x_range=(x_center-50000, x_center+50000), y_range=(y_center-50000, y_center+50000),
           x_axis_type="mercator", y_axis_type="mercator", sizing_mode='stretch_width', tools="pan,wheel_zoom,reset", height=400, width=400)
source = ColumnDataSource(data=dict(x=[], y=[]))

#tile_provider = get_provider(Vendors.CARTODBPOSITRON)
tile_provider = get_provider(Vendors.OSM)
p.add_tile(tile_provider, retina="true")
p.axis.visible = False


p.circle(x='x', y='y', size=10, color='red', alpha=0.8, source=source)

#url = "https://upload.wikimedia.org/wikipedia/commons/e/ed/Map_pin_icon.svg"  # Example URL

# Add a ColumnDataSource for the image marker
#image_source = ColumnDataSource(data=dict(url=[url], x=[], y=[]))
#p.add_glyph(image_source, ImageURL(url="url", x="x", y="y", w=30, h=30, anchor="center"))

p.on_event('tap', update_plot)

# Enable wheel zoom tool and set it as the active scroll tool
wheel_zoom = WheelZoomTool()
p.add_tools(wheel_zoom)
p.toolbar.active_scroll = wheel_zoom
# Define form inputs
auth_input = pn.widgets.TextInput(name='Autentiseringnyckel', placeholder='', width=500)
auth_link = pn.pane.HTML('<a href="https://dev.netatmo.com/apps/" target="_blank">Autentiseringsnyckel kan hämtas här</a>', sizing_mode='stretch_width')
info2 = pn.pane.HTML('Använd kartan för att välja koordinater', sizing_mode='stretch_width')
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=30)

start_date_input = pn.widgets.DatePicker(name='Startdatum', value=start_date, start=datetime.date(2015, 12, 31))
end_date_input = pn.widgets.DatePicker(name='Slutdatum', value=end_date, start=datetime.date(2015, 12, 31))

latitude_input = pn.widgets.TextInput(name='Latitud', value='', width=300)
longitude_input = pn.widgets.TextInput(name='Longitud', value='', width=300)

amount_input = pn.widgets.IntInput(name='Antal stationer', value=1, step=1, start=1)
time_input = pn.widgets.Select(name='Upplösning', options=['30 min', '1 timme', '3 timmar', '1 dag', '1 vecka', '1 månad'])

submit_button = pn.widgets.Button(name='Hämta data', button_type='primary')
submit_button.on_click(submit)
error_div = Div(text="") # add margins
#error_div.text = "Fungerar detta" 
# Download button (initially invisible)
file_download_button = pn.widgets.FileDownload(
    auto=True, 
    button_type='success', 
    embed=False,
    visible=False
)

info_message = "0"
download_message = Div(text="") 

info_box = None # se till att detta är en förklaring till hur man laddar ner nyckeln
loading = pn.indicators.LoadingSpinner(value=False, width=50, height=50,visible=False)

info_button = pn.widgets.Button(name='🛈', width=15, margin=1, align=('start', 'center'), button_type="default", button_style='outline')
info_button.on_click(show_modal)

markdown_text = """## Appens  syfte

Appen hämtar öppet tillgänglig regndata från Netatmo från deras regnmätare uppsatta av privatpersoner och skapar en excel fil med ett antal olika datavyer.

Appen fungerar genom att välja en punkt på kartan och antal regnmätare att hämta, vilken upplösning datan ska ha och perioden då data ska hämtas. Programmet hämtar de X antal närmaste mätarna runt den angivna punken, där antal stationer väljs av användaren. 

## Tokennyckel
För att kunna hämta data automatiskt behöver man en ”Access token”, vilket är en kod för att kunna identifiera en användare för webbplatsen. Nedan beskrivs hur man skapar en ”Access token” för Netatmo.

1.	Gå till https://dev.netatmo.com/apps/ 
2.	För att logga in på Netatmo ska följande uppgifter användas:

Konto: xxxx
Lösen: XXXXXXXXXX  

3.	Under ”My apps” klicka på appen ”Hämta regndata”.
4.	Scrolla ner tills du ser en rubrik som heter ”Token generator”. I menyn välj ”read_station” och klicka på ”Generate token”. Man behöver sen acceptera att det skapas en token, klicka ”Accept” i fönstret som dyker upp. 

Efter man accepterat kan man se ett fält med ”Access token” som man kan kopiera och använda. Den är giltig i 3 timmar, sen behöver man gå in och skapa en ny token via ”Token generator” igen.  Klistra in nyckeln i fältet ”Autentiseringstoken” på originalsidan för att sen börja använda appen.

Ifall för många förfrågningar/hämtningar har gjorts från Netatmo måste en ny nyckel användas, då från en annan "app". Välj då appen "Hämta regndata 2" och hämta nyckel med samma metod som innan. """
# Function to create the Panel app layout
def my_panel_app():
    logging.info("New session created")

    final_layout = pn.Column(pn.Row(
        pn.Column(
            pn.Row(auth_input, info_button),
            auth_link,
            pn.Row(start_date_input, end_date_input),
            pn.Row(latitude_input, longitude_input),
            info2,
            pn.Row(amount_input, time_input),
            download_message,
            pn.Row(submit_button),
            loading,
            error_div,
            width=700)
        , p, width=1400),
        file_download_button)
    ui.main.append(final_layout)
    ui.servable()

ui = pn.template.BootstrapTemplate(favicon="images/favicon2.png", 
                                   site="Hämta regndata från Netatmo", title="")
ui.modal.append(pn.Column())
# Initialize and serve the Panel app
my_panel_app()
