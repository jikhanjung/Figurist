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
import json
import re

DATABASE_FILENAME = fg.PROGRAM_NAME + ".db"
database_path = os.path.join(fg.DEFAULT_DB_DIRECTORY, DATABASE_FILENAME)
gDatabase = SqliteDatabase(database_path,pragmas={'foreign_keys': 1})

def update_taxon_figure( taxon, figure):
    taxfig = FgTaxonFigure.select().where(FgTaxonFigure.figure == figure, FgTaxonFigure.taxon == taxon)
    if taxfig.count() == 0:
        taxfig = FgTaxonFigure()
        taxfig.taxon = taxon
        taxfig.figure = figure
        taxfig.save()

def update_taxon_reference( taxon, reference):
    # find if taxon-reference relationship already exists
    taxref = FgTaxonReference.select().where(FgTaxonReference.taxon == taxon, FgTaxonReference.reference == reference)
    if taxref.count() == 0:
        taxref = FgTaxonReference()
        taxref.taxon = taxon
        taxref.reference = reference
        taxref.save()

def find_parent_for_genus_name(genus_name):
    if genus_name == "Undetermined":
        return None
    return None

def process_taxon_name(taxon_name, taxon_rank = "Species", reference_abbr = None):
    if taxon_name is None:
        return None
    taxon_name = taxon_name.strip()
    comments = ""
    if reference_abbr:
        comments = "Reference:" + reference_abbr + "\n"
    
    # finding "sp. nov." or "n. sp." in the taxon name
    new_species_string = [ "sp. nov.", "n. sp.", "nov. sp.", "sp.nov.", "n.sp."]
    for new_species in new_species_string:
        if new_species in taxon_name:
            comments += taxon_name
            if reference_abbr is not None:
                comments += " in " + reference_abbr 
            comments += "\n"
            taxon_name = taxon_name.replace(new_species, "")
            taxon_name = taxon_name.strip()
            taxon_rank = "Species"

    # regular expression for Authorname, Year
    author_year_string = r"(\(*[A-Z][a-z]+, \d{4}\)*)"
    author_year = re.search(author_year_string, taxon_name)
    if author_year is not None:
        author_year_result = author_year.group(1)
        taxon_name = taxon_name.replace(author_year.group(0), "")
        taxon_name = taxon_name.strip()  
        comments += "Author, Year: " + author_year_result + "\n"
        #comments += "Year: " + year + "\n"

    # author list in the form of "Author1 et Author2" or "Author1 and Author2" or "Author1 & Author2" enclosed in () or not
    #author_list_string = r"(\w+)( et | and | & )(\w+)"
    author_list_string = r"(\(*[A-Z][a-z]+)( et | and | & )([A-Z][a-z]+\)*)"
    author_list = re.search(author_list_string, taxon_name)
    if author_list is not None:
        author = author_list.group(1) + " & " + author_list.group(3)
        taxon_name = taxon_name.replace(author_list.group(0), "")
        taxon_name = taxon_name.strip()  
        comments += "Author: " + author + "\n"

    if taxon_name[-1] == ",":
        taxon_name = taxon_name[:-1]
        taxon_name = taxon_name.strip()
    
    # final attempt to find author name
    #
    # if the last word's first letter is in uppercase and the last word is all alphabets
    #if len(taxon_word_list) > 2 and taxon_word_list[-1][0] 
    # inline 
    def name_check(taxon_name):
        taxon_word_list = taxon_name.split(" ")
        if len(taxon_word_list) > 2 and len(taxon_word_list[-1]) > 1 and taxon_word_list[-1][0].isupper() and taxon_word_list[-1].isalpha():
            author_name = taxon_word_list[-1]
            taxon_name = " ".join(taxon_word_list[:-1])
            return True, taxon_name, author_name
        else:
            return False, taxon_name, None

    #taxon_word_list = taxon_name.split(" ")
    last_word_is_name, taxon_name, author_name = name_check(taxon_name)
    while last_word_is_name:
        comments += "Author: " + author_name + "\n"
        last_word_is_name, taxon_name, author_name = name_check(taxon_name)
        #comments += "Author: " + author + "\n"

    is_undetermined = False
    genus_name = ""
    undetermined_list = [ "undetermined", "Undetermined", "indeterminate", "indet." ]
    for undetermined_string in undetermined_list:
        if undetermined_string in taxon_name:
            comments += "Undetermined: " + undetermined_string + "\n"
            is_undetermined = True
            genus_name = "Undetermined"
            #taxon_name = taxon_name.replace(undetermined_string, "")
            #taxon_name = taxon_name.strip()
    
    taxon = FgTaxon.select().where(FgTaxon.name == taxon_name)
    if taxon.count() > 0:
        taxon = taxon[0]
    else:
        taxon = FgTaxon()
        taxon.name = taxon_name
        name_list = taxon.name.split(" ")
        taxon.parent = None
        taxon.comments = comments
        #taxon.rank = self.edtTaxonRank.text()
        if is_undetermined or len(name_list) == 1:
            if is_undetermined:
                genus_name = "Undetermined"
            else:
                genus_name = name_list[0].replace("?","")
            genus, created = FgTaxon.get_or_create(name=genus_name)
            #print("genus:",genus)
            genus.rank = "Genus"
            genus_parent = find_parent_for_genus_name(genus_name)
            if genus_parent is not None:
                genus.parent = genus_parent
            genus.save()
            taxon.parent = genus
            taxon.rank = "Species"
        else:
            taxon.rank = taxon_rank
        taxon.save()
    return taxon

class FgCollection(Model):
    name = CharField(default='',null=True)
    description = TextField(null=True)
    parent = ForeignKeyField('self', backref='children', null=True,on_delete="CASCADE")
    zotero_library_id = CharField(null=True)
    zotero_key = CharField(null=True)
    zotero_version = CharField(null=True)
    zotero_data = TextField(null=True)
    is_expanded = BooleanField(default=False)
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

    def get_export_name(self):
        #abbr = self.get_abbr()
        #if 
        export_name = "[Col_{}] {}".format(self.id, self.name)
        if self.zotero_key is not None and self.zotero_key != '':
            export_name += " [" + self.zotero_key + "]"
        return export_name

    def export_collection(self, base_path = fg.DEFAULT_STORAGE_DIRECTORY):
        export_path = os.path.join(base_path, self.get_export_name())
        #export_path = os.path.join(base_path, self.name)
        #if self.zotero_key is not None and self.zotero_key != '':
        #    export_path += "[" + self.zotero_key + "]"
        if not os.path.exists(export_path):
            os.makedirs(export_path)

        for ref in self.get_references():
            ref.export_reference(export_path)

        for child in self.children:
            child.export_collection(export_path)

        # export collection info file
        collection_info_file_path = os.path.join(export_path, "collection_info.json")
        collection_data = {
            "name": self.name,
            "description": self.description,
            "zotero_library_id": self.zotero_library_id,
            "zotero_key": self.zotero_key,
            "zotero_version": self.zotero_version,
        }
        with open(collection_info_file_path, 'w', encoding='utf-8') as collection_info_file:
            json.dump(collection_data, collection_info_file, ensure_ascii=False, indent=2)

        return export_path
    
    def import_collection(self, collection_path, parent_collection=None):
        #print('import collection', collection_path)
        collection_info_file_path = os.path.join(collection_path, "collection_info.json")
        if not os.path.exists(collection_info_file_path):
            return False
        
        with open(collection_info_file_path, 'r', encoding='utf-8') as collection_info_file:
            collection_data = json.load(collection_info_file)
            self.name = collection_data["name"]
            self.description = collection_data["description"]
            self.zotero_library_id = collection_data["zotero_library_id"]
            self.zotero_key = collection_data["zotero_key"]
            self.zotero_version = collection_data["zotero_version"]
            if parent_collection is not None:
                self.parent = parent_collection
            self.save()
        # get the list of subcollections that are directories in the collection path and begins with "[Col_{id}]"
        subcollections = [d for d in os.listdir(collection_path) if os.path.isdir(os.path.join(collection_path, d)) and d.startswith("[Col_")]        
        for subcollection in subcollections:
            new_collection = FgCollection()
            new_collection.import_collection(os.path.join(collection_path, subcollection), self)
        # get the list of references that are directories in the collection path and begins with "[Ref_{id}]"
        references = [d for d in os.listdir(collection_path) if os.path.isdir(os.path.join(collection_path, d)) and d.startswith("[Ref_")]
        for reference in references:
            new_reference = FgReference()
            new_reference.import_reference(os.path.join(collection_path, reference), self)

        return True

    def delete_instance(self, recursive=False, delete_nullable=False):
        #print('delete collection instance')
        
        with gDatabase.atomic():
            # First, get all reference IDs associated with this collection
            refs_to_check = (FgReference
                             .select(FgReference.id)
                             .join(FgCollectionReference)
                             .where(FgCollectionReference.collection == self))
            ref_ids = [ref.id for ref in refs_to_check]

            # Now delete the collection (this will also delete associated CollectionReferences due to CASCADE)
            super().delete_instance(recursive, delete_nullable)

            # Check each reference and delete if it's no longer associated with any collection
            for ref_id in ref_ids:
                ref = FgReference.get_or_none(FgReference.id == ref_id)
                if ref and not ref.collections.count():
                    ref.delete_instance()

class FgReference(Model):
    title = CharField(default='',null=True)
    author = CharField(null=True)
    journal = CharField(null=True)
    year = CharField(null=True)
    volume = CharField(null=True)
    issue = CharField(null=True)
    pages = CharField(null=True)
    doi = CharField(null=True)
    url = CharField(null=True)
    zotero_library_id = CharField(null=True)
    zotero_key = CharField(null=True)
    zotero_version = CharField(null=True)
    zotero_data = TextField(null=True)
    abbreviation = CharField(null=True)
    capture_complete = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

    def get_attachment_path(self):
        return os.path.join(fg.DEFAULT_ATTACHMENT_DIRECTORY, str(self.zotero_key))

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
    
    def get_export_name(self):
        #abbr = self.get_abbr()
        #if 
        export_name = "[Ref_{}] {}".format(self.id, self.get_abbr())
        if self.zotero_key is not None and self.zotero_key != '':
            export_name += " [{}]".format(self.zotero_key)
        return export_name

    def export_reference(self, base_path = fg.DEFAULT_STORAGE_DIRECTORY):

        # make sure export path exists
        export_path = os.path.join(base_path, self.get_export_name())
        if not os.path.exists(export_path):
            os.makedirs(export_path)

        # export figure
        figure_info_file_path = os.path.join(export_path, "figure_info.json")        
        figure_data = []        
        for fig in self.figures:
            fig.export_figure_file(export_path)
            #shutil.copyfile(self.get_file_path(), os.path.join(reference_path, self.figure_number + ".png"))
            figure_data.append({
                "id": fig.id,
                "figure_number": fig.figure_number,
                "file_name": fig.figure_number + ".png",
                "file_path": fig.file_path,
                "part1_prefix": fig.part1_prefix,
                "part1_number": fig.part1_number,
                "part2_prefix": fig.part2_prefix,
                "part2_number": fig.part2_number,
                "part_separator": fig.part_separator,                
                "caption": fig.caption,
                "comments": fig.comments,
                "taxon_name": fig.taxon_name,
            })
        with open(figure_info_file_path, 'w', encoding='utf-8') as figure_info_file:
            json.dump(figure_data, figure_info_file, ensure_ascii=False, indent=2)

        # export reference info file
        reference_info_file_path = os.path.join(export_path, "reference_info.json")
        reference_data = {
            "title": self.title,
            "author": self.author,
            "journal": self.journal,
            "year": self.year,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "doi": self.doi,
            "url": self.url,
            "abbreviation": self.abbreviation,
            "zotero_library_id": self.zotero_library_id,
            "zotero_key": self.zotero_key,
            "zotero_version": self.zotero_version,
        }
        with open(reference_info_file_path, 'w', encoding='utf-8') as reference_info_file:
            json.dump(reference_data, reference_info_file, ensure_ascii=False, indent=2)

        # attachments export
        attachment_info_file_path = os.path.join(export_path, "attachment_info.json")
        attachment_data = []
        for attachment in self.attachments:
            attachment_data.append({
                "id": attachment.id,
                "title": attachment.title,
                "filetype": attachment.filetype,
                "filename": attachment.filename,
                "zotero_library_id": attachment.zotero_library_id,
                "zotero_key": attachment.zotero_key,
                "zotero_version": attachment.zotero_version,
            })
            attachment.export_attachment_file(export_path)
        with open(attachment_info_file_path, 'w', encoding='utf-8') as attachment_info_file:
            json.dump(attachment_data, attachment_info_file, ensure_ascii=False, indent=2)

        return True

    class Meta:
        database = gDatabase

    def import_reference(self, reference_path, parent_collection=None):
        #print('import reference', reference_path)
        reference_info_file_path = os.path.join(reference_path, "reference_info.json")
        if not os.path.exists(reference_info_file_path):
            return False
        
        with open(reference_info_file_path, 'r', encoding='utf-8') as reference_info_file:
            reference_data = json.load(reference_info_file)
            self.title = reference_data["title"]
            self.author = reference_data["author"]
            self.journal = reference_data["journal"]
            self.year = reference_data["year"]
            self.volume = reference_data["volume"]
            self.issue = reference_data["issue"]
            self.pages = reference_data["pages"]
            self.doi = reference_data["doi"]
            self.url = reference_data["url"]
            self.abbreviation = reference_data["abbreviation"]
            self.zotero_library_id = reference_data["zotero_library_id"]
            self.zotero_key = reference_data["zotero_key"]
            self.zotero_version = reference_data["zotero_version"]
            self.save()
            if parent_collection is not None:
                FgCollectionReference.create(collection=parent_collection, reference=self)
        # get the list of figures that are directories in the reference path and begins with "[Fig_{id}]"
        figure_info_file = os.path.join(reference_path, "figure_info.json")
        if os.path.exists(figure_info_file):
            with open(figure_info_file, 'r', encoding='utf-8') as figure_info_file:
                figure_data = json.load(figure_info_file)
                for fig in figure_data:
                    new_figure = FgFigure()
                    new_figure.reference = self
                    new_figure.file_name = fig["file_name"]
                    new_figure.file_path = fig["file_path"]
                    new_figure.part1_prefix = fig["part1_prefix"]
                    new_figure.part1_number = fig["part1_number"]
                    new_figure.part2_prefix = fig["part2_prefix"]
                    new_figure.part2_number = fig["part2_number"]
                    new_figure.part_separator = fig["part_separator"]
                    new_figure.update_figure_number()
                    new_figure.caption = fig["caption"]
                    if 'comments' in fig:
                        new_figure.comments = fig["comments"]
                    else:
                        new_figure.comments = ''
                    new_figure.taxon_name = fig["taxon_name"]
                    new_figure.save()
                    new_figure.add_file(os.path.join(reference_path, new_figure.figure_number + ".png" ))
                    if fig["taxon_name"] is not None and fig["taxon_name"].strip() != '':
                        taxon = process_taxon_name(fig["taxon_name"])
                        update_taxon_figure(taxon, new_figure)
                        update_taxon_reference(taxon, self)
                    else:
                        pass
                        #print("taxon is None", new_figure, fig["taxon_name"], self.get_abbr())

        # get the list of attachments that are directories in the reference path and begins with "[Att_{id}]"
        attachment_info_file = os.path.join(reference_path, "attachment_info.json")
        if os.path.exists(attachment_info_file):
            with open(attachment_info_file, 'r', encoding='utf-8') as attachment_info_file:
                attachment_data = json.load(attachment_info_file)
                for att in attachment_data:
                    new_attachment = FgAttachment()
                    new_attachment.reference = self
                    new_attachment.title = att["title"]
                    new_attachment.filetype = att["filetype"]
                    new_attachment.filename = att["filename"]
                    new_attachment.zotero_library_id = att["zotero_library_id"]
                    new_attachment.zotero_key = att["zotero_key"]
                    new_attachment.zotero_version = att["zotero_version"]
                    new_attachment.save()
                    # open and read file content
                    with open(os.path.join(reference_path, new_attachment.filename), "rb") as f:
                        new_attachment.save_file(f.read())
                    #new_attachment.export_attachment_file(os.path.join(reference_path, new_attachment.filename))
        return True

    def delete_instance(self, recursive=False, delete_nullable=False):
        #print('delete collection instance')
        
        with gDatabase.atomic():
            # figure IDs are deleted by cascade so no need to worry about them.
            # attachments same
            # but reference-taxon relation needs to be addressed
            # First, get all taxon IDs associated with this reference
            #taxa_to_check = (FgTaxon
            taxa_to_check = (FgTaxon
                             .select(FgTaxon.id)
                             .join(FgTaxonReference)
                             .where(FgTaxonReference.reference == self))
            taxa_ids = [taxon.id for taxon in taxa_to_check]

            # Now delete the collection (this will also delete associated CollectionReferences due to CASCADE)
            super().delete_instance(recursive, delete_nullable)

            # Check each reference and delete if it's no longer associated with any collection
            for taxon_id in taxa_ids:
                taxon = FgTaxon.get_or_none(FgTaxon.id == taxon_id)
                if taxon and not taxon.related_references.count():
                    taxon.delete_instance()

class FgAttachment(Model):
    reference = ForeignKeyField(FgReference, backref='attachments',on_delete="CASCADE")
    title = CharField(default='',null=True)
    filetype = CharField(null=True)
    filename = CharField(null=True)
    zotero_library_id = CharField(null=True)
    zotero_key = CharField(null=True)
    zotero_version = CharField(null=True)
    zotero_data = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

    def get_file_path(self):
        return os.path.join(fg.DEFAULT_ATTACHMENT_DIRECTORY, str(self.reference.id), str(self.id) + ".pdf")

    def save_file(self, attachment_file):
        attachment_path = self.get_file_path()
        dirname = os.path.dirname(attachment_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        #attachment_filename = os.path.join(attachment_path)
        # get file from zotero
        with open(attachment_path, "wb") as f:
            f.write(attachment_file)

    def export_attachment_file(self, base_path = fg.DEFAULT_STORAGE_DIRECTORY):
        shutil.copyfile(self.get_file_path(), os.path.join(base_path, self.filename))
        return True

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
    comments = TextField(null=True)
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
    part_separator = CharField(null=True,default='-')
    caption = TextField(null=True)
    taxon_name = CharField(null=True)
    comments = TextField(null=True)
    reference = ForeignKeyField(FgReference, backref='figures', null=True,on_delete="CASCADE")
    #taxon = ForeignKeyField(FgTaxon, backref='figures', null=True)
    parent = ForeignKeyField('self', backref='children', null=True,on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.datetime.now)
    modified_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = gDatabase

    def get_sort_key(self):
        def parse_part(part):
            if part is None or part == '':
                return (0, '')
            try:
                return (1, int(part))
            except ValueError:
                return (2, part.lower())

        return (parse_part(self.part1_number), parse_part(self.part2_number))

    def get_taxon_name(self):
        if self.related_taxa.count() > 0:
            return self.related_taxa[0].taxon.name
        else:
            return ""

    def update_figure_number(self):
        if self.part1_number is not None:
            self.figure_number = str(self.part1_prefix) + str(self.part1_number)
            if self.part2_number is not None:
                separator = self.part_separator or ""
                self.figure_number += separator + str(self.part2_prefix) + str(self.part2_number)
            return self.figure_number
        else:
            return self.figure_number

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
        self.load_file_info(file_name)
        new_filepath = self.get_file_path()
        if not os.path.exists(os.path.dirname(new_filepath)):
            os.makedirs(os.path.dirname(new_filepath))
        shutil.copyfile(file_name, new_filepath)
        self.create_thumbnail()
        return self
    
    def add_pixmap(self, pixmap):
        new_filepath = self.get_file_path()
        if not os.path.exists(os.path.dirname(new_filepath)):
            os.makedirs(os.path.dirname(new_filepath))
        pixmap.save(new_filepath)
        self.create_thumbnail()
        return self

    def get_thumbnail_path(self, base_path=fg.DEFAULT_STORAGE_DIRECTORY):
        return os.path.join(base_path, str(self.reference.id), f"{self.id}_thumbnail.png")

    def create_thumbnail(self):
        original_path = self.get_file_path()
        if not os.path.exists(original_path):
            print(f"Error: Original file does not exist at {original_path}")
            return None

        thumbnail_path = self.get_thumbnail_path()
        
        if os.path.exists(thumbnail_path):
            # get time of thumbnail_path
            thumbnail_stat = os.stat(thumbnail_path)
            # get time of original_path
            original_stat = os.stat(original_path)
            # if thumbnail is newer than original, return thumbnail_path
            if thumbnail_stat.st_mtime > original_stat.st_mtime:
                return thumbnail_path

        thumbnail_size = (200, 200)  # You can adjust this size as needed

        try:
            with Image.open(original_path) as img:
                img.thumbnail(thumbnail_size)
                
                # Ensure the directory exists
                os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                
                img.save(thumbnail_path, "PNG")
            return thumbnail_path
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None

    def get_or_create_thumbnail(self):
        thumbnail_path = self.get_thumbnail_path()
        if not os.path.exists(thumbnail_path):
            return self.create_thumbnail()
        return thumbnail_path

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

    def export_figure_file(self, reference_path = fg.DEFAULT_STORAGE_DIRECTORY):
        shutil.copyfile(self.get_file_path(), os.path.join(reference_path, self.figure_number + ".png"))
        return True

    def delete_instance(self, recursive=False, delete_nullable=False):
        #print('delete collection instance')
        
        with gDatabase.atomic():
            # figure IDs are deleted by cascade so no need to worry about them.
            # attachments same
            # but reference-taxon relation needs to be addressed
            # First, get all taxon IDs associated with this reference
            #taxa_to_check = (FgTaxon
            taxa_to_check = (FgTaxon
                             .select(FgTaxon.id)
                             .join(FgTaxonFigure)
                             .where(FgTaxonFigure.figure == self))
            taxa_ids = [taxon.id for taxon in taxa_to_check]

            # Now delete the collection (this will also delete associated CollectionReferences due to CASCADE)
            super().delete_instance(recursive, delete_nullable)

            # Check each reference and delete if it's no longer associated with any collection
            for taxon_id in taxa_ids:
                taxon = FgTaxon.get_or_none(FgTaxon.id == taxon_id)
                if taxon and not taxon.related_figures.count():
                    taxon.delete_instance()

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
