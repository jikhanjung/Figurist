import os
import re
from datetime import datetime

def read_migration_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Extract the migrate function content
    migrate_match = re.search(r'def migrate\(.*?\):(.*?)(?=\n\S|\Z)', content, re.DOTALL)
    if migrate_match:
        return migrate_match.group(1).strip()
    return None

def consolidate_migrations(input_dir, output_file):
    migrations = []
    
    # Read all migration files
    for filename in sorted(os.listdir(input_dir)):
        if filename.endswith('.py'):
            file_path = os.path.join(input_dir, filename)
            migration_content = read_migration_file(file_path)
            if migration_content:
                migrations.append((filename, migration_content))
    
    # Generate consolidated migration file
    with open(output_file, 'w') as outfile:
        outfile.write("from peewee_migrate import Migrator\n\n")
        outfile.write("def migrate(migrator: Migrator, database, **kwargs):\n")
        
        for filename, content in migrations:
            outfile.write(f"    # From {filename}\n")
            outfile.write(content)
            outfile.write("\n\n")

if __name__ == "__main__":
    input_directory = "dev_migrations"
    output_filename = f"release_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    consolidate_migrations(input_directory, output_filename)
    print(f"Consolidated migration script created: {output_filename}")