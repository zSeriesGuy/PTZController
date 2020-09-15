import cherrypy
from . import logger


class CameraControl(object):

    def __init__(self, ptzcontroller):
        self.ptzcontroller = ptzcontroller

    @cherrypy.expose
    def index(self):
        return "CameraControl"

    def _get_camera(self, id):
        args = cherrypy.request.query_string.split('&')
        logger.debug("Control Request: %s %s" % (cherrypy.request.path_info.strip('/'), args))
        camera = self.ptzcontroller.get_camera(id)
        if camera and camera.isconnected:
            return camera
        elif camera:
            logger.debug(f'Camera {camera.name} is not connected.')
        return None

    @cherrypy.expose
    def gotoPreset(self, camera=None, preset=None, **kwargs):
        camera = self._get_camera(camera)
        if camera:
            status = camera.goto_preset(preset)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_presets(self, camera=None):
        camera = self._get_camera(camera)
        preset_list = []
        if camera:
            presets = camera.get_presets()
            for preset in presets:
                preset_list.append({'name': preset.Name, 'num': preset.token})
        return sorted(preset_list, key=lambda key: int(key['num']))

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def set_preset(self, camera=None, preset=None, **kwargs):
        camera = self._get_camera(camera)
        if camera and preset:
            camera.set_preset(preset_token=preset, preset_name=preset)


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def remove_preset(self, camera=None, preset=None, **kwargs):
        camera = self._get_camera(camera)
        if camera and preset:
            camera.remove_preset(preset_token=preset)


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_status(self, camera=None):
        camera = self._get_camera(camera)
        if camera:
            status = camera.get_status()
            return status


    @cherrypy.expose
    def move(self, camera=None, pan=0, tilt=0, zoom=0, velocity=None, **kwargs):
        camera = self._get_camera(camera)
        if camera:
            camera.move_continuous((pan, tilt, zoom))

    @cherrypy.expose
    def stop(self, camera=None, **kwargs):
        camera = self._get_camera(camera)
        if camera:
            camera.stop()

    @cherrypy.expose
    def home(self, camera=None, **kwargs):
        camera = self._get_camera(camera)
        if camera:
            status = camera.go_home()

    @cherrypy.expose
    def focus(self, camera=None, speed=1, **kwargs):
        camera = self._get_camera(camera)
        if camera:
            status = camera.set_focus_mode(mode="MANUAL")
            status = camera.move_focus_continuous(speed=speed)

    @cherrypy.expose
    def focusstop(self, camera=None, **kwargs):
        camera = self._get_camera(camera)
        if camera:
            status = camera.stop_focus()


    """
    Process commands from PTZOptics OBS Dockable Plugin
    """
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def param_cgi(self, camera=None, preset=None, **kwargs):
        logger.info("param: %s" % kwargs)
        return "CameraControl param"


    @cherrypy.expose
    def ptzctrl_cgi(self, camera=1, **kwargs):
        args = cherrypy.request.query_string.split('&')

        if args[0] != 'ptzcmd':
            return

        if args[1] == 'poscall':
            status = self.gotoPreset(camera, int(args[2]) - 1)
        elif args[1] == 'right':
            status = self.move(camera=camera, pan=-int(int(args[2])/20), tilt=0, zoom=0)
        elif args[1] == 'left':
            status = self.move(camera=camera, pan=int(int(args[2])/20), tilt=0, zoom=0)
        elif args[1] == 'up':
            status = self.move(camera=camera, pan=0, tilt=-int(int(args[2])/15), zoom=0)
        elif args[1] == 'down':
            status = self.move(camera=camera, pan=0, tilt=int(int(args[2])/15), zoom=0)
        elif args[1] == 'zoomin':
            status = self.move(camera=camera, pan=0, tilt=0, zoom=int(int(args[2])/7))
        elif args[1] == 'zoomout':
            status = self.move(camera=camera, pan=0, tilt=0, zoom=-int(int(args[2])/7))
        elif args[1] == 'zoomstop':
            status = self.stop(camera)
        elif args[1] == 'ptzstop':
            status = self.stop(camera)
        elif args[1] == 'focusin':
            status = self.focus(camera, speed=int(int(args[2])/7))
        elif args[1] == 'focusout':
            status = self.focus(camera, speed=-int(int(args[2])/7))
        elif args[1] == 'focusstop':
            status = self.focusstop(camera)
        elif args[1] == 'home':
            status = self.home(camera)
        else:
            logger.debug("Unrecogized ptzctrl.ptzcmd: %s" % cherrypy.request.query_string)

