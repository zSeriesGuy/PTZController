import os
from datetime import datetime

import cherrypy
from mako.lookup import TemplateLookup
from mako import exceptions

from . import logger
from .CameraControl import CameraControl

class CameraWeb(object):

    def __init__(self, ptzcontroller):
        self.ptzcontroller = ptzcontroller
        self.template_dir = os.path.join(str(ptzcontroller.PROG_DIR), 'html/')
        self._hplookup = TemplateLookup(directories=[self.template_dir], default_filters=['unicode', 'h'])
        self.http_root = '/'
        self.server_name = 'PTZController'
        self.cache_param = '?V1.0.0'
        self.cameraControl = CameraControl(ptzcontroller)

    @cherrypy.expose
    def index(self):
        return self.serve_template(templatename="index.html", title="Home", cameras=self.ptzcontroller.cameras)

    @cherrypy.expose
    def OBSDock(self):
        return self.serve_template(templatename="OBSDock.html")

    @cherrypy.expose
    def get_status(self):
        x = self.cameraControl.get_status()
        return self.serve_template(templatename="index.html", title="Home", cameras=self.ptzcontroller.cameras)


    def serve_template(self, templatename, **kwargs):
        cache_param = self.cache_param + '.' +  datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        try:
            template = self._hplookup.get_template(templatename)
            return template.render(http_root=self.http_root,
                                   server_name=self.server_name,
                                   cache_param=cache_param,
                                   **kwargs)
        except:
            return exceptions.html_error_template().render()
