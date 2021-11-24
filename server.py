#!/usr/bin/env python3
from quart import Quart, render_template, request
from govle import color,govle
from config import *

app = Quart(__name__)

default_device = devices["office"]

@app.route("/api/v1/power", methods=["POST"])
async def api_power():
    data = await request.json
    async with govle.Govle(default_device) as gle:
        await gle.set_power(data['state'])
    return {}

@app.route("/api/v1/color", methods=["POST"])
async def api_color():
    data = await request.json
    async with govle.Govle(default_device) as gle:
        rgb = color.from_string(data['color'])
        await gle.set_color(rgb)
    return {}

@app.route("/")
async def index():
    return await render_template('index.html')


if __name__ == "__main__":
    app.run()
