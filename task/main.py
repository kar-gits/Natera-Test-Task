# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import xmltodict
import datetime
from translate import Translator


"""
create a data model class for the data
create a GET endpoint “/result” with sorted data returned in the following 4 categories in the order specified and each category sorted per sub bullet point
genes with high risk
same category, count the number of high risk conditions from high to low
genes with high risk and inconclusive
same category, count the number of high risk conditions from high to low
genes with inconclusive but no high risk
same category, count the number of inconclusive conditions from high to low
genes with low risk only
same category, count the number of low risk conditions from high to low
although the data is small example, the code logic should work with arbitrary number of genes and arbitrary number of conditions
"""

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

@app.get("/result", response_class=HTMLResponse)
async def result(request: Request):
    data = [
            {
            "gene": "gene1",
            "riskCategories": [
            {"condition": "disease1", "risk": "high"},
            {"condition": "disease2", "risk": "low"}
            ]},
            {
            "gene": "gene2",
            "riskCategories": [
            {"condition": "disease3", "risk": "inconclusive"},
            {"condition": "disease4", "risk": "low"}
            ]},
            {
            "gene": "gene3",
            "riskCategories": [
            {"condition": "disease3", "risk": "high"},
            {"condition": "disease2", "risk": "high"}
            ]},
            {
            "gene": "gene4",
            "riskCategories": [
            {"condition": "disease3", "risk": "high"},
            {"condition": "disease5", "risk": "inconclusive"}
            ]},
            {
            "gene": "gene5",
            "riskCategories": [
            {"condition": "disease1", "risk": "inconclusive"}
            ]},
            {
            "gene": "gene6",
            "riskCategories": [
            {"condition": "disease2", "risk": "low"}
            ]}
            ]
    res = {}
    
    for d in data:
        rankings = {"high": 0,
                "inconclusive": 0,
                "low": 0}
        for risk in d['riskCategories']:
            if risk['risk'] == 'high':
                rankings[risk['risk']] += 1
            elif risk['risk'] == 'inconclusive':
                rankings[risk['risk']] += 1
            else:
                rankings[risk['risk']] += 1
        res[d['gene']] = rankings
    
    high_risk = {}
    high_and_inconclusive = {}
    inconclusive_only = {}
    low_risk_only = {}

    for gene, conditions in res.items():
        high = conditions['high']
        inconclusive = conditions['inconclusive']
        low = conditions['low']
        
        if high > 0:
            if inconclusive > 0:
                high_and_inconclusive[gene] = high
            else:
                high_risk[gene] = high
        elif inconclusive > 0:
            inconclusive_only[gene] = inconclusive
        elif low > 0:
            low_risk_only[gene] = low

    # Sorting the categories based on the counts (from high to low)
    high_risk_sorted = dict(sorted(high_risk.items(), key=lambda item: item[1], reverse=True))
    high_and_inconclusive_sorted = dict(sorted(high_and_inconclusive.items(), key=lambda item: item[1], reverse=True))
    inconclusive_only_sorted = dict(sorted(inconclusive_only.items(), key=lambda item: item[1], reverse=True))
    low_risk_only_sorted = dict(sorted(low_risk_only.items(), key=lambda item: item[1], reverse=True))

    return templates.TemplateResponse(
        request=request, name="result_template.html", context={"result": [high_risk_sorted, high_and_inconclusive_sorted, inconclusive_only_sorted, low_risk_only_sorted]}
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
