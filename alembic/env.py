from db.database import Base
from db.models import *
import os
from sqlalchemy import engine_from_config, pool
from alembic import context

target_metadata = Base.metadata
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mealmaster.db")
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)
fileconfig = config.get_section(config.config_ini_section)