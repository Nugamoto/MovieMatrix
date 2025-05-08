from sqlalchemy import create_engine

from datamanager.models import Base

# Create SQLite file and engine
engine = create_engine('sqlite:///moviematrix.sqlite')

# Create all tables defined in the models
Base.metadata.create_all(engine)

print("✔️ Database successfully created.")
