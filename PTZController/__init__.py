import os
import sys

try:
    import webbrowser
    no_browser = False
except ImportError:
    no_browser = True

import cherrypy

from . import logger
from .config import Config
from .camera import Camera
from . import CameraWeb, CameraConfig, CameraControl



class PTZController(object):
    FULL_PATH = None
    PROG_DIR = None
    SYS_PLATFORM = None
    SYS_LANGUAGE = None
    SYS_ENCODING = None
    ARGS = None
    SIGNAL = None
    CONFIG = None
    VERBOSE = False
    QUIET = False

    def __init__(self, args):
        self.ARGS = args

        self.VERBOSE = True if args.verbose else False
        self.QUIET = True if args.quiet else False

        # Initialize the configuration
        if args.config:
            config_file = args.config
        else:
            config_file = os.path.join(self.PROG_DIR, config.FILENAME)
        self.CONFIG = Config(config_file)

        # Initialize Logging
        log_dir = self.CONFIG.get('General', 'log_dir', fallback='logs')
        if log_dir == 'None':
            log_dir = None
            log_writable = False
        else:
            log_dir, log_writable = self.check_folder_writable(log_dir, os.path.join(self.PROG_DIR, 'logs'), 'logs')
            if not log_writable and not self.QUIET:
                sys.stderr.write("Unable to create the log directory. Logging to screen only.\n")

        logger.initLogger(console=not self.QUIET, log_dir=log_dir if log_writable else None, verbose=self.VERBOSE)

        logger.info("PTZController Initializing")

        # Initialize the camera configurations
        self.initialize_cameras()

        # Initialize the WebServer
        options = {
            'log.screen': False,
            'log.access_file': '',
            'log.error_file': '',
            'server.thread_pool': 10,
        }

        options['server.socket_port'] = self.CONFIG.getint('Webserver', 'server_port', fallback=8080)
        if self.CONFIG.getboolean('Webserver', 'remote', fallback=False):
            options['server.socket_host'] = '0.0.0.0'

        cherrypy.config.update(options)

        conf = {
            '/': {
                'tools.staticdir.root': os.path.join(self.PROG_DIR, 'html'),
                'tools.gzip.on': True,
                'tools.gzip.mime_types': ['text/html', 'text/plain', 'text/css',
                                          'text/javascript', 'application/json',
                                          'application/javascript'],
                'tools.auth.on': False,
                'tools.auth_basic.on': False,
                'tools.sessions.on': True,
                'tools.encode.on': True,
                'tools.encode.encoding': 'utf-8',
                'tools.decode.on': True,
                'tools.response_headers.on': True,
                'tools.response_headers.headers': [('Access-Control-Allow-Origin', '*')],
            },
            '/images': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': "images",
                'tools.staticdir.content_types': {'svg': 'image/svg+xml'},
                'tools.caching.on': True,
                'tools.caching.force': True,
                'tools.caching.delay': 0,
                'tools.expires.on': True,
                'tools.expires.secs': 60 * 60 * 24 * 30,  # 30 days
                'tools.sessions.on': False,
                'tools.auth.on': False
            },
            '/css': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': "css",
                'tools.caching.on': True,
                'tools.caching.force': True,
                'tools.caching.delay': 0,
                'tools.expires.on': True,
                'tools.expires.secs': 60 * 60 * 24 * 30,  # 30 days
                'tools.sessions.on': False,
                'tools.auth.on': False
            },
            '/fonts': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': "fonts",
                'tools.caching.on': True,
                'tools.caching.force': True,
                'tools.caching.delay': 0,
                'tools.expires.on': True,
                'tools.expires.secs': 60 * 60 * 24 * 30,  # 30 days
                'tools.sessions.on': False,
                'tools.auth.on': False
            },
            '/js': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': "js",
                'tools.caching.on': True,
                'tools.caching.force': True,
                'tools.caching.delay': 0,
                'tools.expires.on': True,
                'tools.expires.secs': 60 * 60 * 24 * 30,  # 30 days
                'tools.sessions.on': False,
                'tools.auth.on': False
            },
        }

        cherrypy.tree.mount(CameraWeb.CameraWeb(self), '/', config=conf)
        cherrypy.tree.mount(CameraConfig.CameraConfig(self), '/config', config=conf)
        cherrypy.tree.mount(CameraControl.CameraControl(self), '/control', config=conf)
        cherrypy.tree.mount(CameraControl.CameraControl(self), '/cgi-bin', config=conf)
        cherrypy.log.access_log.propagate = False
        cherrypy.server.start()
        cherrypy.server.wait()

        if self.CONFIG.getboolean('General', 'launch_browser', fallback=True) and not args.nolaunch and not no_browser:
            host = 'localhost'
            port = options['server.socket_port']
            root = '/'
            protocol = 'http'
            try:
                webbrowser.open('%s://%s:%i%s' % (protocol, host, port, root))
            except Exception as e:
                logger.error("Could not launch browser: %s" % e)

        logger.info("PTZController Initialization Complete")

    @property
    def cameras(self):
        return self._cameras

    def shutdown(self, restart=False, update=False, checkout=False):
        print("Stopping PTZController...")
        cherrypy.engine.exit()
        print('WebServices Terminated')

    def initialize_cameras(self):
        self._cameras = []
        cameraID = 1
        for section in self.CONFIG.sections():
            if section in ['General', 'Webserver']:
                continue
            camera_options = {}
            camera_options['id'] = cameraID
            for key, value in self.CONFIG.items(section):
                if key == 'id':
                    continue
                camera_options[key] = value
            if 'name' not in camera_options:
                camera_options['name'] = section[0:12] if len(section) > 12 else section
            self._cameras.append(Camera(camera_options))
            cameraID += 1

    def get_camera(self, id=None):
        try:
            id = int(id)
            for camera in self._cameras:
                if camera.id == id:
                    return camera
        except (TypeError, ValueError):
            pass
        logger.debug(f'Invalid Camera ID: {id}')
        return None

    def check_folder_writable(self, folder, fallback, name):
        if not folder:
            folder = fallback

        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except OSError as e:
                logger.error("Could not create %s dir '%s': %s" % (name, folder, e))
                if folder != fallback:
                    logger.warn("Falling back to %s dir '%s'" % (name, fallback))
                    return self.check_folder_writable(None, fallback, name)
                else:
                    return folder, None

        if not os.access(folder, os.W_OK):
            logger.error("Cannot write to %s dir '%s'" % (name, folder))
            if folder != fallback:
                logger.warn("Falling back to %s dir '%s'" % (name, fallback))
                return self.check_folder_writable(None, fallback, name)
            else:
                return folder, False

        return folder, True
