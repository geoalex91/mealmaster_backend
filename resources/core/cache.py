from db.database import SessionLocal
from db.models import Ingredients
from resources.logger import Logger
from resources.searching import IngredientSearch
from routers.schemas import IngredientsSummary
from collections import defaultdict
from threading import Lock
from sqlalchemy.orm import Session
import time, threading

_usage_lock = Lock()
TRIE_CACHE_LIMIT = 1000

def sync_usage_to_db():
    while True:
        time.sleep(600)  # 10 minutes
        with _usage_lock:
            updates = dict(ingredient_cache.ingredient_usage_cache)
            ingredient_cache.ingredient_usage_cache.clear()

        db: Session = SessionLocal()
        try:
            for ing_id, count in updates.items():
                db.query(Ingredients).filter(Ingredients.id == ing_id).update(
                    {"usage_count": Ingredients.usage_count + count}
                )
            db.commit()
        finally:
            db.close()

def start_sync_thread():
    thread = threading.Thread(target=sync_usage_to_db, daemon=True)
    thread.start()

class IngredientCache:
    def __init__(self):
        self.logger = Logger()
        self.search_index = IngredientSearch()
        self.ingredient_usage_cache = defaultdict(int)

    def build_cache(self):
        db = SessionLocal()
        try:
            ingredients = (db.query(Ingredients).order_by(Ingredients.usage_count.desc()).limit(TRIE_CACHE_LIMIT).all())
            for ingredient in ingredients:
                summary_ingredient = IngredientsSummary.model_validate(ingredient)
                self.search_index.insert(summary_ingredient)
        except Exception as e:
            self.logger.error(f"Error building ingredient cache: {e}")
        finally:
            db.close()
    
    def add_ingredient(self, ingredient: IngredientsSummary):
        try:
            self.search_index.insert(ingredient)
            self.logger.info(f"Ingredient added to cache: {ingredient.name}")
        except Exception as e:
            self.logger.error(f"Failed to add ingredient to cache: {e}")

    def remove_ingredient(self, ingredient_name: str):
        try:
            self.search_index.delete(ingredient_name)
            self.logger.info(f"Ingredient removed from cache: {ingredient_name}")
        except Exception as e:
            self.logger.error(f"Failed to remove ingredient from cache: {e}")
    
    def rename_ingredient(self, old_name: str, new_name: IngredientsSummary):
        try:
            self.search_index.rename(old_name, new_name)
            self.logger.info(f"Ingredient renamed in cache: {old_name} to {new_name}")
        except Exception as e:
            self.logger.error(f"Failed to rename ingredient in cache: {e}")

    def search_ingredients(self, prefix: str):
        try:
            results = self.search_index.prefix_search(prefix)
            return [r.model_dump() for r in results]
        except Exception as e:
            self.logger.error(f"Error during prefix search: {e}")
            return {}
    
    def fuzzy_search(self, query: str, max_distance: int = 1):
        try:
            results = self.search_index.fuzzy_search(query, max_distance)
            return [r.model_dump() for r in results]
        except Exception as e:
            self.logger.error(f"Error during fuzzy search: {e}")
            return {}
    
    def smart_search(self, query: str, limit: int = 50):
        try:
            results = self.search_index.smart_search(query, limit)
            return [r.model_dump() for r in results]
        except Exception as e:
            self.logger.error(f"Error during smart search: {e}")
            return {}
    
    def increment_usage(self, ingredient: IngredientsSummary):
        try:
            with _usage_lock:
                self.search_index.increment_usage(ingredient)
                self.ingredient_usage_cache[ingredient.id] += 1
        except Exception as e:
            self.logger.error(f"Error incrementing usage for {ingredient.name}: {e}")

ingredient_cache = IngredientCache()