# pyvisualcompare
Graphical tool to help monitor visual changes on web pages

## Why use it?
You might want to use this tool if you are interested in monitoring visual changes in web pages.
For example you may be interested in immediately getting a notification if the latest version of Python changes on python.org. 
In pyvisualcompare you can select an area of a page that announces the latest Python version:

<img src="/img/pyvisualcompare-select.png" alt="Screenshot" width="600px"/>

Another use case can be getting updates on exam result announcements.

It offers an alternative to services like [Visualping](https://visualping.io/) that have significant costs or restrictions on the update rate.
As this tool is supposed to run on your own server, the update rate can be as high as you want (as long as the server can handle it). 

## How to use it?
The process to set up monitoring is not easy, but pyvisualcompare will guide you through it.
It uses an [```urlwatch```](https://github.com/thp/urlwatch) shell command in the background, so all
notification options offered by ```urlwatch``` can be used. Some other tools are needed on the computer that is used to select
the area of interest (frontend PC) as well as on the server that is supposed to periodically check for changes (backend server).

### Frontend (GUI) on Linux

Clone the repository (or download the code as a `zip` file):

```bash
git clone https://github.com/nspo/pyvisualcompare.git
cd pyvisualcompare/
```

On the frontend, the following packages must be installed (example for Ubuntu/Debian systems):

```sudo apt install python3-pyqt5 wkhtmltopdf xvfb```

When all necessary packages are installed on the frontend, pyvisualcompare can be started with ```python3 main.py```
and the URL of interest can be entered. All other steps are (hopefully) explained in the interface.

### Frontend (GUI) with Docker

The following Docker command should make it possible to use the frontend on systems which have a running X11 server (most Linux distributions):

`docker run -it -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY -u qtuser nspohrer/pyvisualcompare python3 /app/main.py`

If you are running MacOS, you will probably have to install XQuartz and adapt the parameters a bit - see [this guide](https://gist.github.com/cschiewek/246a244ba23da8b9f0e7b11a68bf3285).

### Frontend options

#### Static size
You can choose to take a screenshot of the target web page with a static size.
This seems to be necessary for some web pages to work correctly.

#### Delay
If the web page is not yet fully loaded when the virtual screenshot is taken (e.g. due to Javascript), you may want to increase the default delay of 350 ms to a higher value.

### Backend on Linux
The setup wizard will help to install the needed packages on the backend server.

### Backend with Docker

The following code snippet shows an example how you can run the main part of the `pyvisualcompare` backend with Docker (e.g. on MacOS or if you do not want to install system packages):

`docker run -it -u qtuser nspohrer/pyvisualcompare /app/pyvisualcompare-md5.sh --crop-x 8 --crop-y 5 --crop-w 232 --crop-h 58 heise.de`

You will need to adapt the call to `pyvisualcompare-md5.sh` with the parameters you get from the frontend.

### Backend custom parameters

The backend uses `wkhtmltoimage` for rendering web pages into images.
In some use cases, you might want to slightly modify the command the `pyvisualcompare` frontend generates for you.
Parameters for `wkhtmltoimage` can be added in the call to `pyvisualcompare-md5.sh` to change the default behavior.
The full list of possible `wkhtmltoimage` parameters can be found [here](https://wkhtmltopdf.org/usage/wkhtmltopdf.txt).

## How exactly does it work?

* A screenshot of the web page is rendered using [```wkhtmltoimage```](https://wkhtmltopdf.org/) 
* As most backend servers do not have a graphical interface, [```xvfb```](https://packages.debian.org/de/stable/xvfb) is used to imitate an X server. This is necessary due to ```wkhtmltoimage```.
* The cropped screenshot is compared to the original screenshot with an MD5 hash - if there is any change in the image, the hash will be different
* A change would also be detected if e.g. some content is added *above* the area of interest. If this is not acceptable, some other ```urlwatch``` filters might be more adequate.
