"""SQLAlchemy database instance.

Defined here (not in __init__.py) so model modules can import `db` without
creating a circular import back to the application factory.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
