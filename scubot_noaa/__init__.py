"""This file defines the public exports of the scubot_noaa module"""
from .noaa import Noaa
from .noaa import setup

__all__ = ('Noaa', 'setup')
