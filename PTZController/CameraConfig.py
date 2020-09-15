import cherrypy

class CameraConfig(object):

    def __init__(self, ptzcontroller):
        self.ptzcontroller = ptzcontroller

    @cherrypy.expose
    def index(self):
        return "CameraConfig"

