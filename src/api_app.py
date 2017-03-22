#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import gc
from config.url_api import urls2

app = web.application(urls2, globals())
application = app.wsgifunc()

#----------------------------------------

gc.set_threshold(300,5,5)


#if __name__ == "__main__":
#    app = web.application(urls2, globals(), autoreload=True)
#    app.run()
