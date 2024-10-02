import datetime
from peewee_migrate import Router
from peewee import *
from FgModel import *
import FgUtils as fg
import os
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_timestamp():
    import datetime
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d")
migrations_path = fg.resource_path('migrations')
if not os.path.exists(migrations_path):
    os.makedirs(migrations_path)
#migrations_path = "migrations"
print("migrations_path: ", migrations_path)
print("database path: ", database_path)
gDatabase.connect()
tables = gDatabase.get_tables()

print("tables: ", tables)
router = Router(gDatabase, migrate_dir=migrations_path)
print("router: ", router)
# set migration_name to YYYYMMDD_HHMMSS
migration_name = get_timestamp()
print("migration_name: ", migration_name)
ret = router.create(auto=[FgCollection,FgReference,FgCollectionReference,FgTaxon,FgFigure,FgTaxonReference,FgTaxonFigure,FgAttachment,FgTreeOfLife], name=migration_name)
print("ret: ", ret)


