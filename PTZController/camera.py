from threading import Thread

from onvif import ONVIFCamera, ONVIFError
from datetime import timedelta

## MONKEY PATCH
#def zeep_pythonvalue(self, xmlvalue):
#    return xmlvalue

#zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue

#ONVIFCameraControlError = ONVIFError


from . import logger


class Camera(object):
    def __init__(self, options):
        self.id = options['id']
        self.name = options['name']
        self.host = options['host']
        self.port = int(options['port'])
        self.__userid = options['userid']
        self.__password = options['password']
        self.__isconnected = False
        th = Thread(target=self.__initialize, name=f"CameraInit-{self.name}")
        th.start()

    def __initialize(self):
        logger.info(f'Initializing Camera {self.name} at {(self.host,self.port)}')
        try:
            self.__cam = ONVIFCamera(self.host, self.port, self.__userid, self.__password)
            self.__media_service = self.__cam.create_media_service()
            self.__ptz_service = self.__cam.create_ptz_service()
            self.__imaging_service = self.__cam.create_imaging_service()
            self.__profile = self.__media_service.GetProfiles()[0]
            self.__video_source = self.__get_video_sources()[0]
            self.__ptz_status = self.__ptz_service.GetStatus({'ProfileToken': self.__profile.token})
            self.__isconnected = True
            self.capabilities = self.__get_service_capabilities()
            logger.info(f'Successfully Initialized Camera {self.name} at {(self.host, self.port)}')
        except Exception as e:
            self.__isconnected = False
            logger.info(f'Initialization for Camera {self.name} at {(self.host, self.port)} failed. Not Connected')

    @property
    def isconnected(self):
        return self.__isconnected

    @property
    def configuration(self):
        return self.__get_configurations()

    @property
    def configOptions(self):
        return self.__get_ptz_conf_opts()



    def get_stream_uri(self, protocol='UDP', stream='RTP-Unicast'):
        """
        :param protocol
            string 'UDP', 'TCP', 'RTSP', 'HTTP'
        :param stream
             string either 'RTP-Unicast' or 'RTP-Multicast'
        WARNING!!!
        Some cameras return invalid stream uri

        RTP unicast over UDP: StreamType = "RTP_Unicast", TransportProtocol = "UDP"
        RTP over RTSP over HTTP over TCP: StreamType = "RTP_Unicast", TransportProtocol = "HTTP"
        RTP over RTSP over TCP: StreamType = "RTP_Unicast", TransportProtocol = "RTSP"
        """
        logger.debug(f'Camera {self.name}: Getting stream uri {protocol} {stream}')
        req = self.__media_service.create_type('GetStreamUri')
        req.ProfileToken = self.__profile.token
        req.StreamSetup = {'Stream': stream, 'Transport': {'Protocol': protocol}}
        return self.__media_service.GetStreamUri(req)

    def get_status(self):
        return self.__ptz_service.GetStatus({'ProfileToken': self.__profile.token})

    def go_home(self):
        logger.debug(f'Camera {self.name}: Moving home')
        req = self.__ptz_service.create_type('GotoHomePosition')
        req.ProfileToken = self.__profile.token
        self.__ptz_service.GotoHomePosition(req)

    def get_presets(self):
        logger.debug(f'Camera {self.name}: Getting presets')
        return self.__ptz_service.GetPresets(self.__profile.token)

    def goto_preset(self, preset_token, ptz_velocity=(1.0, 1.0, 1.0)):
        """
        :param preset_token:
            unsigned int
        :param ptz_velocity:
            tuple (pan,tilt,zoom) where
            pan tilt and zoom in range [0,1]
        """
        logger.debug(f'Camera {self.name}: Moving to preset {preset_token}, speed={ptz_velocity}')
        req = self.__ptz_service.create_type('GotoPreset')
        req.ProfileToken = self.__profile.token
        req.PresetToken = preset_token
        req.Speed = self.__ptz_status.Position
        vel = req.Speed
        vel.PanTilt.x, vel.PanTilt.y = ptz_velocity[0], ptz_velocity[1]
        vel.Zoom.x = ptz_velocity[2]
        return self.__ptz_service.GotoPreset(req)

    def set_preset(self, preset_token=None, preset_name=None):
        """
        :param preset_token:
            unsigned int, usually in range [1, 128] dependent on camera
        :param preset_name:
            string
            if None then duplicate preset_token
        """
        logger.debug(f'Camera {self.name}: Setting preset {preset_token} ({preset_name})')
        req = self.__ptz_service.create_type('SetPreset')
        req.ProfileToken = self.__profile.token
        req.PresetToken = preset_token
        req.PresetName = preset_name
        return self.__ptz_service.SetPreset(req)

    def remove_preset(self, preset_token=None, preset_name=None):
        """
        :param preset_token:
            unsigned int, usually in range [1, 128] dependent on camera
        :param preset_name:
            string
            if None then duplicate preset_token
        """
        logger.debug(f'Camera {self.name}: Removing preset {preset_token}')
        req = self.__ptz_service.create_type('RemovePreset')
        req.ProfileToken = self.__profile.token
        req.PresetToken = preset_token
        return self.__ptz_service.RemovePreset(req)

    def stop(self):
        logger.debug(f'Camera {self.name}: Stopping movement')
        self.__ptz_service.Stop({'ProfileToken': self.__profile.token})

    def get_brightness(self):
        logger.debug(f'Camera {self.name}: Getting brightness')
        imaging_settings = self.__get_imaging_settings()
        return imaging_settings.Brightness

    def set_brightness(self, brightness):
        """
        :param brightness:
            float in range [0, 100]
        """
        logger.debug(f'Camera {self.name}: Settings brightness')
        imaging_settings = self.__get_imaging_settings()
        imaging_settings.Brightness = brightness
        self.__set_imaging_settings(imaging_settings)

    def get_color_saturation(self):
        logger.debug(f'Camera {self.name}: Getting color_saturation')
        imaging_settings = self.__get_imaging_settings()
        return imaging_settings.ColorSaturation

    def set_color_saturation(self, color_saturation):
        """
        :param color_saturation:
            float in range [0, 100]
        """
        logger.debug(f'Camera {self.name}: Settings color_saturation')
        imaging_settings = self.__get_imaging_settings()
        imaging_settings.ColorSaturation = color_saturation
        self.__set_imaging_settings(imaging_settings)

    def get_contrast(self):
        logger.debug(f'Camera {self.name}: Getting contrast')
        imaging_settings = self.__get_imaging_settings()
        return imaging_settings.Contrast

    def set_contrast(self, contrast):
        """
        :param contrast:
            float in range [0, 100]
        """
        logger.debug(f'Camera {self.name}: Settings contrast')
        imaging_settings = self.__get_imaging_settings()
        imaging_settings.Contrast = contrast
        self.__set_imaging_settings(imaging_settings)

    def get_sharpness(self):
        logger.debug(f'Camera {self.name}: Getting sharpness')
        imaging_settings = self.__get_imaging_settings()
        return imaging_settings.Sharpness

    def set_sharpness(self, sharpness):
        """
        :param sharpness:
            float in range [0, 100]
        """
        logger.debug(f'Camera {self.name}: Settings sharpness')
        imaging_settings = self.__get_imaging_settings()
        imaging_settings.Sharpness = sharpness
        self.__set_imaging_settings(imaging_settings)

    def set_focus_mode(self, mode='AUTO'):
        """
        :param mode:
            string, can be either 'AUTO' or 'MANUAL'
        """
        logger.debug(f'Camera {self.name}: Settings focus mode')
        imaging_settings = self.__get_imaging_settings()
        imaging_settings.Focus.AutoFocusMode = mode
        self.__set_imaging_settings(imaging_settings)

    def move_focus_continuous(self, speed):
        """
        :param speed:
            float in range [-1,1]
        """
        logger.debug(f'Camera {self.name}: Doing move focus continuous')
        req = self.__imaging_service.create_type('Move')
        req.VideoSourceToken = self.__video_source.token
        req.Focus = self.__get_move_options()
        req.Focus.Continuous.Speed = speed
        self.__imaging_service.Move(req)

    def move_focus_absolute(self, position, speed=1):
        """
        :param position:
            float in range [0,1]
        :param speed:
            float in range [0,1]
        """
        logger.debug(f'Camera {self.name}: Doing move focus absolute')
        req = self.__imaging_service.create_type('Move')
        req.VideoSourceToken = self.__video_source.token
        req.Focus = self.__get_move_options()
        req.Focus.Absolute.Position = position
        req.Focus.Absolute.Speed = speed
        self.__imaging_service.Move(req)

    def stop_focus(self):
        logger.debug(f'Camera {self.name}: Stopping focus')
        self.__imaging_service.Stop(self.__video_source.token)

    def move_continuous(self, ptz_velocity, timeout=None):
        """
        :param ptz_velocity:
            tuple (pan,tilt,zoom) where
            pan tilt and zoom in range [-1,1]
        """
        logger.debug(f'Camera {self.name}: Continuous move {ptz_velocity} {"" if timeout is None else " for " + str(timeout)}')
        req = self.__ptz_service.create_type('ContinuousMove')
        req.Velocity = self.__ptz_status.Position
        req.ProfileToken = self.__profile.token
        vel = req.Velocity
        vel.PanTilt.x, vel.PanTilt.y = float(ptz_velocity[0]), float(ptz_velocity[1])
        vel.Zoom.x = float(ptz_velocity[2])
        # force default space
        vel.PanTilt.space, vel.Zoom.space = None, None
        if timeout is not None:
            if type(timeout) is timedelta:
                req.Timeout = timeout
            else:
                raise TypeError('Camera {self.name}: timeout parameter is of datetime.timedelta type')
        self.__ptz_service.ContinuousMove(req)

    def move_absolute(self, ptz_position, ptz_velocity=(1.0, 1.0, 1.0)):
        logger.debug(f'Camera {self.name}: Absolute move {ptz_position}')
        req = self.__ptz_service.create_type['AbsoluteMove']
        req.ProfileToken = self.__profile.token
        pos = req.Position
        pos.PanTilt.x, pos.PanTilt.y = ptz_position[0], ptz_position[1]
        pos.Zoom.x = ptz_position[2]
        vel = req.Speed
        vel.PanTilt.x, vel.PanTilt.y = ptz_velocity[0], ptz_velocity[1]
        vel.Zoom.x = ptz_velocity[2]
        self.__ptz_service.AbsoluteMove(req)

    def move_relative(self, ptz_position, ptz_velocity=(1.0, 1.0, 1.0)):
        logger.debug(f'Camera {self.name}: Relative move {ptz_position}')
        req = self.__ptz_service.create_type['RelativeMove']
        req.ProfileToken = self.__profile.token
        pos = req.Translation
        pos.PanTilt.x, pos.PanTilt.y = ptz_position[0], ptz_position[1]
        pos.Zoom.x = ptz_position[2]
        vel = req.Speed
        vel.PanTilt.x, vel.PanTilt.y = ptz_velocity[0], ptz_velocity[1]
        vel.Zoom.x = ptz_velocity[2]
        self.__ptz_service.RelativeMove(req)

    def __get_move_options(self):
        logger.debug(f'Camera {self.name}: Getting Move Options')
        req = self.__imaging_service.create_type('GetMoveOptions')
        req.VideoSourceToken = self.__video_source.token
        return self.__imaging_service.GetMoveOptions(req)

    def __get_options(self):
        logger.debug(f'Camera {self.name}: Getting options')
        req = self.__imaging_service.create_type('GetOptions')
        req.VideoSourceToken = self.__video_source.token
        return self.__imaging_service.GetOptions(req)

    def __get_video_sources(self):
        logger.debug(f'Camera {self.name}: Getting video source configurations')
        req = self.__media_service.create_type('GetVideoSources')
        return self.__media_service.GetVideoSources(req)

    def __get_ptz_conf_opts(self):
        logger.debug(f'Camera {self.name}: Getting configuration options')
        req = self.__ptz_service.create_type('GetConfigurationOptions')
        req.ConfigurationToken = self.__profile.PTZConfiguration.token
        return self.__ptz_service.GetConfigurationOptions(req)

    def __get_configurations(self):
        logger.debug(f'Camera {self.name}: Getting configurations')
        req = self.__ptz_service.create_type('GetConfigurations')
        return self.__ptz_service.GetConfigurations(req)[0]

    def __get_node(self, node_token):
        logger.debug(f'Camera {self.name}: Getting node {node_token}')
        req = self.__ptz_service.create_type('GetNode')
        req.NodeToken = node_token
        return self.__ptz_service.GetNode(req)

    def __set_imaging_settings(self, imaging_settings):
        logger.debug(f'Camera {self.name}: Setting imaging settings')
        req = self.__imaging_service.create_type('SetImagingSettings')
        req.VideoSourceToken = self.__video_source.token
        req.ImagingSettings = imaging_settings
        return self.__imaging_service.SetImagingSettings(req)

    def __get_imaging_settings(self):
        logger.debug(f'Camera {self.name}: Getting imaging settings')
        req = self.__imaging_service.create_type('GetImagingSettings')
        req.VideoSourceToken = self.__video_source.token
        return self.__imaging_service.GetImagingSettings(req)

    def __get_service_capabilities(self):
        logger.debug(f'Camera {self.name}: Getting capabilities')
        return self.__ptz_service.GetServiceCapabilities()
