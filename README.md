# PTZController

PTZController is a python3-based webserver application for controlling ONVIF-capable PTZ cameras.
It includes a webpage for controlling velocity, direction, and presets. There is also a webpage browser dock page for OBS Studio for quick access to Presets.

## Installation
* Download or Clone this repository.
* Open a command or terminal window.
* CD to where you unzipped or cloned the repository.
* Create a Virtual Environment:
    * Type: `python -m venv .\venv`
* Activate the Virtual Environment:
    * On Windows, type: `.\venv\scripts\activate`
    * On Linux, type: `source ./venv/bin/activate`
* Type: `python -m pip install --upgrade pip setuptools`
* Type: `pip install -r requirements.txt`
* Start the server: 
    * On Windows, type: `.\venv\scripts\python3 start.py`
    * On Linux, type: `./venv/bin/python start.py`
* PTZController will be loaded in your browser and listening on <http://localhost:8080>
> **NOTE:** You can use `Start PTZController.bat` to start the server on Windows.

## Configuration
The configuration parameters are stored in `PTZController.conf`.
An example is provided in `example.PTZController.conf`. Copy it to `PTZController.conf` to get started.
Use your favorite editor to edit the configuration.

There are multiple sections:
##### General
* log_dir: Location to store a log. None means no logging.
* launch_browser: Whether or not to launch a browser window when the server starts.

##### Webserver
* server_port: What port do you want the server to listen on. Defaults to 8080.
* remote: (yes or no) With "no", this server listens only on localhost. With "yes", this server is accessible remotely.

##### Any other sections not named General or Webserver are considered to be cameras.
* host: The IP address or hostname of the PTZ camera.
* port: The port that ONVIF listens on in the camera.
* userid and password: The credentials for accessing ONVIF on the camera.
* Name (optional): The name to use for the camera. If no name is specified, the section name is used as the camera name. Note that only the first 12 characters are used for the name. This name is what is listed in the Camera Selector.

## Usage
### Webpage Usage
The webpage contains four sections: Camera Selector, PTZ Controls, Presets, and a Joystick.

##### Camera Selector
This section is only visible if there is more than one camera defined. Select the camera that you want to control.

##### PTZ Controls
This section has buttons to move the camera up/down/left/right/home.
The plus/minus toggle button is for zoom control.
The next toggle button is for focus control. 
The slider is speed control.

##### Presets
This section lists the presets that are configured on the camera.
Use the gear to edit the presets. You can add a new preset or update and existing preset. Click the checkmark to complete the editing. 
Use the circle button to refresh the list of presets.

##### Joystick
This section is a virtual joystick that allows control of both velocity and direction.

### OBS Studio Usage
You can add a Presets selection page to OBS Studio.

* In OBS Studio, select View->Docks->Custom Browser Docs..
* Give the Dock a name such as Presets.
* Define the URL to access the webserver, ie. `http://localhost:8080/OBSDock`

The webserver has command recognition so that any ONVIF camera should work with the PTZOptics plugin for OBS Studio.

## CREDITS
* MikhaelMIEM/ONVIFCameraControl for the original ONVIF camera access code.
* bobboteck/JoyStick for the javascript joystick code. 