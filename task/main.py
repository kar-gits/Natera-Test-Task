# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import xmltodict
import datetime
from translate import Translator

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/en", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
async def page_load(request: Request):
    data = await process_data()
    return templates.TemplateResponse(
        request=request, name="template.html", context={"data": data[0], "date": data[1]}
    )

@app.get("/es", response_class=HTMLResponse)
async def es_page_load(request: Request):
    data = await process_data()
    translator= Translator(to_lang="es")
    for idx, item in enumerate(data[0]):
        data[0][idx]['es_title'] = translator.translate(item['title'])
    return templates.TemplateResponse(
        request=request, name="es_template.html", context={"data": data[0], "date": data[1]}
    )

async def process_data():
    namespaces = {
        'http://search.yahoo.com/mrss/': None,
        'http://purl.org/dc/elements/1.1/': None
        }
    url = "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"
    response = requests.get(url)
    data = xmltodict.parse(response.content, attr_prefix='', process_namespaces=True, namespaces=namespaces)
    items = data.get("rss").get("channel").get("item")
    now = datetime.datetime.now()
    formatted_time = now.strftime("%a, %d %b %Y")
    required_data = []
    for item in items:
        datetime_obj = datetime.datetime.strptime(str(item.get('pubDate', '')), '%a, %d %b %Y %H:%M:%S %z')
        temp_data = {}
        temp_data['title'] = item.get('title', '')
        temp_data['pub_date'] = datetime_obj.strftime('%b %d, %Y')
        temp_data['description'] = await list_to_string(item.get('description', ''))
        temp_data['creator'] = item.get('creator', '')
        temp_data['link'] = item.get('link', '#')
        temp_data['image_url'] = item.get('content', '...')
        if temp_data['image_url'] != '...':
            temp_data['image_url'] = item.get('content', '...').get('url', '...')
        required_data.append(temp_data)
    
    return [required_data, formatted_time]

async def list_to_string(data):
    if type(data) == list:
        return " ".join(data)
    return data
