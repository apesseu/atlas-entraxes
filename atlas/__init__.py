"""
Atlas Entraxes - Package principal

Ce package contient l'application Dash pour la visualisation
des altitudes maximales par département.
"""

__version__ = "1.0.0"
__author__ = "apesseu"
__description__ = "Atlas Entraxes - Visualisation moderne des altitudes maximales"

# Imports principaux pour faciliter l'accès
from . import app
from . import config
from . import utils

__all__ = ["app", "config", "utils"]
