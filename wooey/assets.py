# -*- coding: utf-8 -*-
from flask.ext.assets import Bundle, Environment

css = Bundle(
    "css/style.css",
    filters="cssmin",
    output="public/css/common.css"
)

js = Bundle(
    "js/plugins.js",
    "js/script.js",
    filters='jsmin',
    output="public/js/common.js"
)

assets = Environment()

assets.register("js_all", js)
assets.register("css_all", css)
