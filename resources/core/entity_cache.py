from ast import List
from typing import Type
from pydantic import BaseModel
from db.database import SessionLocal
from db.models import Ingredients, Recipes
from resources.logger import Logger
from resources.core.search_engine import ObjectSearchTrie
from routers.schemas import IngredientsSummary, RecipeSummary
from collections import defaultdict
from threading import Lock
from sqlalchemy.orm import Session
import time, threading

TRIE_CACHE_LIMIT = 1000
ING_MAX_TRIE_DEPTH = 64
REC_MAX_TRIE_DEPTH = 64
USAGE_WEIGHT = 0.8
PREFIX_BOOST_WEIGHT = 0.2
DISTANCE_WEIGHT = 1.0

class EntityCache:
    def __init__(self, search_trie: ObjectSearchTrie, model_cls: Type, summary_cls: Type[BaseModel]):
        self.logger = Logger()
        self.search_index = search_trie
        self.ingredient_usage_cache = defaultdict(int)
        self.model_cls = model_cls
        self.summary_cls = summary_cls
        # Track number of cached items
        self._cached_ids = set()
        self._usage_lock = Lock()

    def build_cache(self):
        db = SessionLocal()
        try:
            items = (db.query(self.model_cls).order_by(self.model_cls.usage_count.desc()).limit(TRIE_CACHE_LIMIT).all())
            for ingredient in items:
                summary_ingredient = self.summary_cls.model_validate(ingredient)
                self.search_index.insert(summary_ingredient)
                self._cached_ids.add(summary_ingredient.id)
            #self.print_tree_in_log_file()
            if self.summary_cls == IngredientsSummary:
                self.logger.info(f"Ingredient cache built with {len(items)} items.")
            else:
                self.logger.info(f"Recipe cache built with {len(items)} items.")
            self.get_depth_()
        except Exception as e:
            self.logger.error(f"Error building ingredient cache: {e}")
        finally:
            db.close()
    
    def add_ingredient(self, ingredient):
        try:
            self.search_index.insert(ingredient)
            self.logger.info(f"element added to cache: {ingredient.name}")
            self._cached_ids.add(ingredient.id)
        except Exception as e:
            self.logger.error(f"Failed to add element to cache: {e}")

    def remove_ingredient(self, ingredient_name: str):
        try:
            self.search_index.delete(ingredient_name)
            self.logger.info(f"Element removed from cache: {ingredient_name}")
            # Lazy cleanup of id set (full scan by name resolution skipped for simplicity)
        except Exception as e:
            self.logger.error(f"Failed to remove element from cache: {e}")

    def rename_ingredient(self, old_name: str, new_name:object):
        try:
            self.search_index.rename(old_name, new_name)
            self.logger.info(f"Element renamed in cache: {old_name} to {new_name}")
        except Exception as e:
            self.logger.error(f"Failed to rename element in cache: {e}")

    def _db_prefix_fallback(self, prefix: str, limit: int):
        db = SessionLocal()
        try:
            items = (db.query(self.model_cls)
                        .filter(self.model_cls.name.ilike(f"{prefix}%"))
                        .order_by(self.model_cls.usage_count.desc())
                        .limit(limit)
                        .all())
            summaries = [self.summary_cls.model_validate(i) for i in items]
            return summaries
        finally:
            db.close()

    def _maybe_promote(self, ing):
        if len(self._cached_ids) < TRIE_CACHE_LIMIT:
            try:
                self.search_index.insert(ing)
                self._cached_ids.add(ing.id)
            except Exception as e:
                self.logger.debug(f"Promotion failed for {ing.id}: {e}")

    def prefix_search(self, prefix: str, limit = 50):
        try:
            results = self.search_index.prefix_search(prefix, limit)
            if len(results) > 5 or len(self._cached_ids) != TRIE_CACHE_LIMIT:
                return [r.model_dump() for r in results[:limit]]
            # Fallback to DB for more matches
            return self._fallback_prefix_search(prefix, results, limit)
        except Exception as e:
            self.logger.error(f"Error during prefix search: {e}")
            return []

    def _fallback_prefix_search(self, prefix: str, results: list, limit: int):
        needed = limit - len(results)
        db_extras = self._db_prefix_fallback(prefix, needed * 2)  # overfetch for ranking
        # Deduplicate
        existing_ids = {r.id for r in results}
        merged: List[IngredientsSummary] = results[:]
        for ing in db_extras:
            if ing.id not in existing_ids:
                merged.append(ing)
                existing_ids.add(ing.id)
                self._maybe_promote(ing)
            if len(merged) >= limit:
                break
        return [m.model_dump() for m in merged[:limit]]
    
    def multi_token_prefix_search(self, query: str, limit: int = 50):
        try:
            # token distance 0 for prefix-like behavior
            results = self.search_index.multi_token_prefix_search(query, limit=limit)
            if len(results) >= limit or len(self._cached_ids) != TRIE_CACHE_LIMIT:
                return [r.model_dump() for r in results[:limit]]
            # DB fallback: fetch names starting with first token
            return self._fallback_multi_token_prefix_search(query, results, limit)
        except Exception as e:
            self.logger.error(f"Error during multi-token prefix search: {e}")
            return []

    def _fallback_multi_token_prefix_search(self, query: str, results: list, limit: int):
        first_tok = query.split()[0]
        db = SessionLocal()
        try:
            rows = (db.query(self.model_cls)
                        .filter(self.model_cls.name.ilike(f"%{first_tok}%"))
                        .order_by(self.model_cls.usage_count.desc())
                        .limit(limit)
                        .all())
        finally:
            db.close()
        existing_ids = {r.id for r in results}
        for row in rows:
            if row.id not in existing_ids:
                ing_sum = self.summary_cls.model_validate(row)
                results.append(ing_sum)
                existing_ids.add(row.id)
                self._maybe_promote(ing_sum)
            if len(results) >= limit:
                break
        return [r.model_dump() for r in results[:limit]]

    def fuzzy_search(self, query: str, max_distance: int = 2, limit: int = 50):
        try:
            if len(query) > 6:
                max_distance += 1
            if len(query) > 10:
                max_distance += 1
            results = self.search_index.fuzzy_search(query, max_distance, limit)
            return [r.model_dump() for r in results[:limit]]
        except Exception as e:
            self.logger.error(f"Error during fuzzy search: {e}")
            return []

    def multi_token_fuzzy_search(self, query: str, limit: int = 50, token_max_distance: int = 1):
        try:
            results = self.search_index.multi_token_fuzzy_search(query, limit=limit, token_max_distance=token_max_distance)
            if len(results) > 5 or len(self._cached_ids) != TRIE_CACHE_LIMIT:
                return [r.model_dump() for r in results[:limit]]
            # If under limit, fallback: fetch candidates containing any query token
            return self.fallback_multi_token_fuzzy_search(query, results, limit)
        except Exception as e:
            self.logger.error(f"Error during multi-token fuzzy search: {e}")
            return []

    def _fallback_multi_token_fuzzy_search(self, query: str, results: list, limit: int):
        tokens = [t for t in query.split() if t]
        if not tokens:
            return []
        pattern = "%" + "%".join(tokens) + "%"  # coarse pattern
        db = SessionLocal()
        try:
            rows = (db.query(Ingredients)
                        .filter(Ingredients.name.ilike(pattern))
                        .order_by(Ingredients.usage_count.desc())
                        .limit(200)
                        .all())
        finally:
            db.close()
        existing_ids = {r.id for r in results}
        for row in rows:
            if row.id in existing_ids:
                continue
            ing_sum = IngredientsSummary.model_validate(row)
            results.append(ing_sum)
            existing_ids.add(row.id)
            self._maybe_promote(ing_sum)
            if len(results) >= limit:
                break
        return [r.model_dump() for r in results[:limit]]
    
    def smart_search(self, query: str, max_distance: int = 2, limit: int = 50):
        try:
            results = self.search_index.smart_search(query, max_distance, limit)
            if len(results) >= limit or len(self._cached_ids) != TRIE_CACHE_LIMIT:
                return [r.model_dump() for r in results[:limit]]
            # Compose remaining using fuzzy + multi-token fallbacks
            prefix_needed = limit - len(results)
            fuzzy_more = self._fallback_multi_token_fuzzy_search(query, results, prefix_needed)
            # fuzzy_more already returns dict dumps; need to parse back to model for merging
            fuzzy_models = []
            for item in fuzzy_more:
                try:
                    fuzzy_models.append(self.summary_cls.model_validate(item))
                except Exception:
                    pass
            combined_ids = {r.id for r in results}
            for fm in fuzzy_models:
                if fm.id not in combined_ids and len(results) < limit:
                    results.append(fm)
                    combined_ids.add(fm.id)
            return [r.model_dump() for r in results[:limit]]
        except Exception as e:
            self.logger.error(f"Error during smart search: {e}")
            return []
    
    def increment_usage(self, ingredient):
        try:
            with self._usage_lock:
                self.search_index.increment_usage(ingredient)
                self.ingredient_usage_cache[ingredient.id] += 1
        except Exception as e:
            self.logger.error(f"Error incrementing usage for {ingredient.name}: {e}")

    def print_tree_in_log_file(self) -> int:
        try:
            self.search_index.print_tree()
        except Exception as e:
            self.logger.error(f"Error printing tree to log file: {e}")
    
    def get_depth_(self) -> int:
        try:
            depth = self.search_index.get_depth()
            self.logger.info(f"Trie depth: {depth}")
            return depth
        except Exception as e:
            self.logger.error(f"Error getting trie depth: {e}")
            return -1

    def sync_usage_to_db(self):
        while True:
            # 10 minutes
            with self._usage_lock:
                updates = dict(ingredient_cache.ingredient_usage_cache)
                ingredient_cache.ingredient_usage_cache.clear()

            db: Session = SessionLocal()
            try:
                for ing_id, count in updates.items():
                    db.query(self.model_cls).filter(self.model_cls.id == ing_id).update(
                        {"usage_count": self.model_cls.usage_count + count}
                    )
                db.commit()
            finally:
                db.close()
                time.sleep(600) # 10 minutes

    def start_sync_thread(self):
        thread = threading.Thread(target=self.sync_usage_to_db, daemon=True)
        thread.start()

ingredient_trie = ObjectSearchTrie(ING_MAX_TRIE_DEPTH, USAGE_WEIGHT, PREFIX_BOOST_WEIGHT, DISTANCE_WEIGHT)
recipe_trie = ObjectSearchTrie(REC_MAX_TRIE_DEPTH, USAGE_WEIGHT, PREFIX_BOOST_WEIGHT, DISTANCE_WEIGHT)
ingredient_cache = EntityCache(ingredient_trie, Ingredients, IngredientsSummary)
recipe_cache = EntityCache(recipe_trie, Recipes, RecipeSummary)