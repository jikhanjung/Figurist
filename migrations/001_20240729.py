"""Peewee migrations -- 001_20240729.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""
    
    @migrator.create_model
    class FgCollection(pw.Model):
        id = pw.AutoField()
        name = pw.CharField(max_length=255)
        description = pw.TextField(null=True)
        parent = pw.ForeignKeyField(column_name='parent_id', field='id', model='self', null=True, on_delete='CASCADE')
        zotero_key = pw.CharField(max_length=255)
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()

        class Meta:
            table_name = "fgcollection"

    @migrator.create_model
    class FgReference(pw.Model):
        id = pw.AutoField()
        title = pw.CharField(max_length=255)
        author = pw.CharField(max_length=255)
        journal = pw.CharField(max_length=255)
        year = pw.CharField(max_length=255)
        volume = pw.CharField(max_length=255)
        issue = pw.CharField(max_length=255)
        pages = pw.CharField(max_length=255)
        doi = pw.CharField(max_length=255)
        url = pw.CharField(max_length=255)
        zotero_key = pw.CharField(max_length=255)
        abbreviation = pw.CharField(max_length=255, null=True)
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()

        class Meta:
            table_name = "fgreference"

    @migrator.create_model
    class FgCollectionReference(pw.Model):
        id = pw.AutoField()
        collection = pw.ForeignKeyField(column_name='collection_id', field='id', model=migrator.orm['fgcollection'], on_delete='CASCADE')
        reference = pw.ForeignKeyField(column_name='reference_id', field='id', model=migrator.orm['fgreference'], on_delete='CASCADE')
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()

        class Meta:
            table_name = "fgcollectionreference"

    @migrator.create_model
    class FgFigure(pw.Model):
        id = pw.AutoField()
        file_name = pw.CharField(max_length=255)
        file_path = pw.CharField(max_length=255)
        figure_number = pw.CharField(max_length=255)
        part1_prefix = pw.CharField(max_length=255, null=True)
        part1_number = pw.CharField(max_length=255, null=True)
        part2_prefix = pw.CharField(max_length=255, null=True)
        part2_number = pw.CharField(max_length=255, null=True)
        caption = pw.TextField(null=True)
        comments = pw.TextField(null=True)
        reference = pw.ForeignKeyField(column_name='reference_id', field='id', model=migrator.orm['fgreference'], null=True, on_delete='CASCADE')
        parent = pw.ForeignKeyField(column_name='parent_id', field='id', model='self', null=True, on_delete='CASCADE')
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()

        class Meta:
            table_name = "fgfigure"

    @migrator.create_model
    class FgTaxon(pw.Model):
        id = pw.AutoField()
        name = pw.CharField(max_length=255)
        rank = pw.CharField(max_length=255, null=True)
        author = pw.CharField(max_length=255, null=True)
        year = pw.CharField(max_length=255, null=True)
        junior_synonym_of = pw.ForeignKeyField(column_name='junior_synonym_of_id', field='id', model='self', null=True)
        parent = pw.ForeignKeyField(column_name='parent_id', field='id', model='self', null=True, on_delete='CASCADE')
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()

        class Meta:
            table_name = "fgtaxon"

    @migrator.create_model
    class FgTaxonFigure(pw.Model):
        id = pw.AutoField()
        taxon = pw.ForeignKeyField(column_name='taxon_id', field='id', model=migrator.orm['fgtaxon'], on_delete='CASCADE')
        figure = pw.ForeignKeyField(column_name='figure_id', field='id', model=migrator.orm['fgfigure'], on_delete='CASCADE')
        reltype = pw.CharField(max_length=255, null=True)
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()

        class Meta:
            table_name = "fgtaxonfigure"

    @migrator.create_model
    class FgTaxonReference(pw.Model):
        id = pw.AutoField()
        taxon = pw.ForeignKeyField(column_name='taxon_id', field='id', model=migrator.orm['fgtaxon'], on_delete='CASCADE')
        reference = pw.ForeignKeyField(column_name='reference_id', field='id', model=migrator.orm['fgreference'], on_delete='CASCADE')
        reltype = pw.CharField(max_length=255, null=True)
        created_at = pw.DateTimeField()
        modified_at = pw.DateTimeField()

        class Meta:
            table_name = "fgtaxonreference"


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""
    
    migrator.remove_model('fgtaxonreference')

    migrator.remove_model('fgtaxonfigure')

    migrator.remove_model('fgtaxon')

    migrator.remove_model('fgfigure')

    migrator.remove_model('fgcollectionreference')

    migrator.remove_model('fgreference')

    migrator.remove_model('fgcollection')
