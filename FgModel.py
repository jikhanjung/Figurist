from peewee import *
import datetime
import os
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import io
from pathlib import Path
import copy
import FgUtils as fg
import shutil

DATABASE_FILENAME = fg.PROGRAM_NAME + ".db"
database_path = os.path.join(fg.DEFAULT_DB_DIRECTORY, DATABASE_FILENAME)
gDatabase = SqliteDatabase(database_path,pragmas={'foreign_keys': 1})

class FgCollection(Model):
    name = CharField()
    description = TextField(null=True)
    parent = ForeignKeyField('self', backref='children', null=True,on_delete="CASCADE")
    zotero_key = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

    def get_references(self):
        ref_list = []
        for colref in self.references:
            ref_list.append(colref.reference)
        return ref_list
        #return self.references

    def export_collection(self, base_path = fg.DEFAULT_STORAGE_DIRECTORY):
        export_path = os.path.join(base_path, self.name)
        if not os.path.exists(export_path):
            os.makedirs(export_path)
        for ref in self.get_references():
            ref.export_reference(export_path)
        for child in self.children:
            child.export_collection(export_path)
        return export_path
    
    def import_collection(self, base_path = fg.DEFAULT_STORAGE_DIRECTORY):
        import_path = os.path.join(base_path, self.name)
        for root, dirs, files in os.walk(import_path):
            for file in files:
                print(os.path.join(root, file))
        return import_path

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
    abbreviation = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

    def add_figure(self, file_path):
        fig = FgFigure()
        fig.reference = self
        fig.parse_file_name(file_path)
        fig.save()
        fig.add_file(file_path)
        return fig

    def get_abbr(self):
        if self.abbreviation is not None:
            return self.abbreviation
        else:
            return self.author + " (" + str(self.year) + ")"
        #return self.author + " (" + str(self.year) + ")"

    def export_reference(self, base_path = fg.DEFAULT_STORAGE_DIRECTORY):
        export_path = os.path.join(base_path, self.get_abbr())
        if not os.path.exists(export_path):
            os.makedirs(export_path)
        for fig in self.figures:
            fig.export_figure(export_path)
        return export_path

class FgCollectionReference(Model):
    collection = ForeignKeyField(FgCollection, backref='references',on_delete="CASCADE")
    reference = ForeignKeyField(FgReference, backref='collections',on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

class FgTaxon(Model):
    name = CharField()
    rank = CharField(null=True)
    author = CharField(null=True)
    year = CharField(null=True)
    junior_synonym_of = ForeignKeyField('self', backref='synonyms', null=True)
    parent = ForeignKeyField('self', backref='children', null=True,on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

class FgFigure(Model):
    file_name = CharField()
    file_path = CharField()
    figure_number = CharField()
    part1_prefix = CharField(null=True)
    part1_number = CharField(null=True)
    part2_prefix = CharField(null=True)
    part2_number = CharField(null=True)
    caption = TextField(null=True)
    comments = TextField(null=True)
    reference = ForeignKeyField(FgReference, backref='figures', null=True,on_delete="CASCADE")
    #taxon = ForeignKeyField(FgTaxon, backref='figures', null=True)
    parent = ForeignKeyField('self', backref='children', null=True,on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

    def get_figure_name(self):
        name = self.figure_number
        if self.related_taxa.count() > 0:
            name += " " + self.related_taxa[0].taxon.name
        return name

    def parse_file_name(self, file_path):
        self.file_name = Path(file_path).name
        self.file_path = file_path
        name = self.file_name

        # remove the directory name from the file name
        directory_name = Path(file_path).parent.name
        name.replace(directory_name, '')
        
        # trim off the extension 
        name_split = name.split('.')
        name = ".".join(name_split[:-1])
        # trim whitespaces
        name = name.strip()

        #taxon name
        #name_split = name.split("_")
        #if len(name_split) > 1:
        #    taxon_name = name_split[0]
        #    if taxon_name.strip() != '':
        #        self.taxon = FgTaxon.get_or_create(name=taxon_name, reference=self.reference)[0]

        # fine figure number in the form of Fig1, Fig1-2, etc
        pl_index = name.find('Pl')
        plate_index = name.find('Plate')
        fig_index = name.find('Fig')
        if pl_index > -1:
            self.figure_number = name[pl_index:]
        elif plate_index > -1:
            self.figure_number = name[plate_index:]
        elif fig_index > -1:
            self.figure_number = name[fig_index:]
        else:
            self.figure_number = str(len(self.reference.figures)+1)

        #taxon_name = name.splitreplace(self.figure_number, '')
        

    def add_file(self, file_name):
        #print("add file:", file_name)
        self.load_file_info(file_name)
        new_filepath = self.get_file_path()
        #print("new file:", new_filepath)
        if not os.path.exists(os.path.dirname(new_filepath)):
            os.makedirs(os.path.dirname(new_filepath))
        #print("new file:", new_filepath)
        ret = shutil.copyfile(file_name, new_filepath)
        #print("ret:", ret)
        return self
    
    def add_pixmap(self, pixmap):
        new_filepath = self.get_file_path()
        #print("new file:", new_filepath)
        if not os.path.exists(os.path.dirname(new_filepath)):
            os.makedirs(os.path.dirname(new_filepath))
        pixmap.save(new_filepath)
        return self

    def load_file_info(self, fullpath):

        file_info = {}

        ''' file stat '''
        stat_result = os.stat(fullpath)
        file_info['mtime'] = stat_result.st_mtime
        file_info['ctime'] = stat_result.st_ctime

        if os.path.isdir(fullpath):
            file_info['type'] = 'dir'
        else:
            file_info['type'] = 'file'

        if os.path.isdir( fullpath ):
            return file_info

        file_info['size'] = stat_result.st_size

        ''' md5 hash value '''
        #file_info['md5hash'], image_data = self.get_md5hash_info(fullpath)

        ''' exif info '''
        #exif_info = self.get_exif_info(fullpath, image_data)
        #file_info['exifdatetime'] = exif_info['datetime']
        #file_info['latitude'] = exif_info['latitude']
        #file_info['longitude'] = exif_info['longitude']
        #file_info['map_datum'] = exif_info['map_datum']

        self.original_path = str(fullpath)
        self.original_filename = Path(fullpath).name
        #self.md5hash = file_info['md5hash']
        self.size = file_info['size']
        #self.exifdatetime = file_info['exifdatetime']
        #self.file_created = file_info['ctime']
        #self.file_modified = file_info['mtime']

    def get_file_path(self, base_path =  fg.DEFAULT_STORAGE_DIRECTORY ):
        return os.path.join( base_path, str(self.reference.id), str(self.id) + "." + str(self.file_name).split('.')[-1])

    def get_md5hash_info(self,filepath):
        return '', ''
        afile = open(filepath, 'rb')
        hasher = hashlib.md5()
        image_data = afile.read()
        hasher.update(image_data)
        afile.close()
        md5hash = hasher.hexdigest()
        return md5hash, image_data

class FgTaxonReference(Model):
    taxon = ForeignKeyField(FgTaxon, backref='related_references',on_delete="CASCADE")
    reference = ForeignKeyField(FgReference, backref='related_taxa',on_delete="CASCADE")
    reltype = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

class FgTaxonFigure(Model):
    taxon = ForeignKeyField(FgTaxon, backref='related_figures',on_delete="CASCADE")
    figure = ForeignKeyField(FgFigure, backref='related_taxa',on_delete="CASCADE")
    reltype = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase
