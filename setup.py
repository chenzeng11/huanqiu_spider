import sys
import os
import time
from random import randint
import platform
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
import logging
from HQWDownParser import HQWDownParser

from cx_Freeze import setup, Executable

base = None

if sys.platform == "win32":
    base = "Win32GUI"
executables = [Executable("runspider.py", base=base)]

packages = [
    "idna",
    "os",
    "time",
    "selenium",
    "logging",
    "pyvirtualdisplay",
    "platform",
    "random",
    "collections",
]
options = {"build_exe": {"packages": packages,'excludes':["tkinter","babel","IPython","notebook","scipy","win32com","matplotlib"]}}

setup(
    name="Spider",
    options=options,
    version="0.0.1",
    description="spider_for_huanqiu",
    executables=executables
)
