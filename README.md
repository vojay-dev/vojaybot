![logo](doc/vojaybot.png)

Hi there, this is an extensible and modular Twitch chat bot and framework based on Python. This was creating during
my live streams on Twitch. Basically it holds a full featured, configurable chat bot that I use myself but the
components of it are easily usable to implement your own bot based on it.

![features](doc/vojaybot-features.png)

## Work in Progress

I am in the progress of writing an introduction on how to use it for your Twitch projects. Feel free to follow my
Twitch Channel to get regular updates: [twitch.tv/vojay](https://twitch.tv/vojay).

## Windows Executable

In case you would like to have a Windows executable, the project comes with a `pyinstaller` dependency. Just run:
```
pyinstaller -F -i "assets/icon.ico" -n "vojay bot" --add-data "config/config.toml;config/config.toml" main.py
```

Which generates a `/dist/vojay bot` folder containing all dependencies and an executable `.exe` file.
