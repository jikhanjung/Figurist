from peewee import *
import datetime
import os
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import io
from pathlib import Path
import copy
import FgUtils as fg

DATABASE_FILENAME = fg.PROGRAM_NAME + ".db"
database_path = os.path.join(fg.DEFAULT_DB_DIRECTORY, DATABASE_FILENAME)
gDatabase = SqliteDatabase(database_path,pragmas={'foreign_keys': 1})

class FgReference(Model):
    title = CharField()
    author = CharField()
    journal = CharField()
    year = CharField()
    volume = CharField()
    issue = CharField()
    pages = CharField()
    doi = CharField()
    url = CharField()
    zotero_key = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

class FgTaxon(Model):
    name = CharField()
    rank = CharField()
    author = CharField()
    year = CharField()
    reference = ForeignKeyField(FgReference, backref='taxa')
    junior_synonym_of = ForeignKeyField('self', backref='synonyms', null=True)
    parent = ForeignKeyField('self', backref='children', null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

class FgFigure(Model):
    file_name = CharField()
    file_path = CharField()
    figure_number = CharField()
    reference = ForeignKeyField(FgReference, backref='figures')
    taxon = ForeignKeyField(FgTaxon, backref='figures')
    parent = ForeignKeyField('self', backref='children', null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase
