# app/pricing/__init__.py
from flask import Blueprint

bp = Blueprint('pricing', __name__)

from . import routes