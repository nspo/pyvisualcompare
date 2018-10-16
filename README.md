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

On the frontend, the following packages must be installed (example for Ubuntu/Debian systems):

```sudo apt install python3-pyqt5 wkhtmltopdf xvfb```

The setup wizard will help to install the needed packages on the backend server.

When all necessary packages are installed on the frontend, pyvisualcompare can be started with ```python3 main.py```
and the URL of interest can be entered. All other steps are (hopefully) explained in the interface.

## How exactly does it work?

* A screenshot of the web page is rendered using [```wkhtmltoimage```](https://wkhtmltopdf.org/) 
* As most backend servers do not have a graphical interface, [```xvfb```](https://packages.debian.org/de/stable/xvfb) is used to imitate an X server. This is necessary due to ```wkhtmltoimage```.
* The cropped screenshot is compared to the original screenshot with an MD5 hash - if there is any change in the image, the hash will be different
* A change would also be detected if e.g. some content is added *above* the area of interest. If this is not acceptable, some other ```urlwatch``` filters might be more adequate.
