#!/usr/bin/env python
# -*- coding: utf-8 -*-

from io import BytesIO
from captcha.image import ImageCaptcha
from base64 import b64encode
from urllib import quote_plus

_image = ImageCaptcha(fonts=['/usr/local/a1.ttf', '/usr/local/a2.ttf'])

def gen_rand_png(rand):
    data = _image.generate(rand).read()
    png = quote_plus(b64encode(data))
    png2 = 'data:image/png;base64,%s'%png

    return png2
