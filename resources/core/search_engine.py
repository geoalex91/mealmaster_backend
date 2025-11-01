from __future__ import annotations
from typing import Dict, List, Set, Tuple
import threading
import unicodedata
from resources.logger import Logger
from abc import ABC, abstractmethod

logger = Logger()

def normalize(text: str) -> str:
    """
    Normalize a string by converting it to lowercase and removing diacritical marks.
    This helps in performing accent-insensitive searches.
    Args:
        s (str): The input string to normalize.
    Returns:
        str: The normalized string.
    """
    # Normalize to NFD form to separate base characters from diacritics
    normalized = unicodedata.normalize('NFD', text)
    # Filter out diacritical marks (category 'Mn')
    without_diacritics = ''.join(
        c for c in normalized if unicodedata.category(c) != 'Mn')
    # Convert to lowercase
    return without_diacritics.lower()

class GenericNode:
    """Base node class for trie structures."""
    def __init__(self):
        """Initializes a GenericNode with children, end-of-word flag, weight, and value."""
        self.children: Dict[str, GenericNode] = {}
        self.is_end_of_word: bool = False
        self.weight = 0
        self.value = None

class TrieNode(GenericNode):
    """Trie node structure for full ingredient names mapping to ingredient summaries."""
    def __init__(self):
        super().__init__()
        self.children: Dict[str, TrieNode] = {}
        
class TokenTrieNode(GenericNode):
    """Separate trie structure for individual tokens (words) mapping to ingredient summaries.

    Each terminal node keeps a set of ingredient references whose names contain that token.
    """
    def __init__(self):
        super().__init__()
        self.children: Dict[str, TokenTrieNode] = {}
        self.items: Set[int] = set()  # Store ingredient IDs (ints) for hashability

class GenericTrieInterface(ABC):
    """Abstract base class defining the interface for a generic trie structure."""
    def __init__(self):
        self.root = GenericNode()
        self._lock = threading.Lock()

    @abstractmethod
    def insert(self, item: object, weight: int = 1):
        """Inserts an item into the trie with an optional weight."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, item: object):
        """Deletes an item from the trie by its name."""
        raise NotImplementedError

    @abstractmethod
    def rename(self, old_item: object, new_item: object):
        """Renames an item in the trie by removing the old name and inserting the new item."""
        raise NotImplementedError

    @abstractmethod
    def prefix_search(self, prefix: str, limit: int = 50) -> List[object]:
        """Performs a prefix search in the trie and returns a list of matching items."""
        raise NotImplementedError

    @abstractmethod
    def fuzzy_search(self, word: str, max_distance: int = 1, limit: int = 50) -> List[object]:
        """Performs a fuzzy search in the trie and returns a list of matching items."""
        raise NotImplementedError
    
    def print_tree_inlog_file(self, node = None, prefix: str = ''):
        """Utility function to print the trie structure to the log file for debugging."""
        if node is None:
            node = self.root
        if node.is_end_of_word:
            print(f"{prefix} (weight: {node.weight})")
            print(f"  {node.value}")
            logger.info(f"{prefix} (weight: {node.weight}) {node.value}")
        for ch, child in node.children.items():
            self.print_tree_inlog_file(child, prefix + ch)

    def get_depth(self) -> int:
        """Get the maximum depth of the trie."""
        def _depth(node, current_depth: int) -> int:
            if not node.children:
                return current_depth
            return max(_depth(child, current_depth + 1) for child in node.children.values())
        with self._lock:
            return _depth(self.root, 0)
    
    def increment_usage(self, item: object):
        """Increments the usage count (weight) of an item in the trie."""
        node = self.root
        for ch in item.name.lower():
            if ch not in node.children:
                return
            node = node.children[ch]
        if node.is_end_of_word:
            node.weight += 1
            node.value.usage_count = node.weight
    
class SearchTrie(GenericTrieInterface):
    """Trie structure for full ingredient names mapping to ingredient summaries."""
    def __init__(self,max_trie_depth: int = 64, distance_weight: float = 1.0):
        super().__init__()
        self.root = TrieNode()
        self.distance_weight = distance_weight  # multiplier for distance in ordering
        self.max_trie_depth = max_trie_depth   # Traversal guard

    def insert(self, item: object, weight: int = 1):
        """Inserts an item into the trie with an optional weight.
        Args:
            item: The item to insert into the trie.
            weight: The weight to assign to the item (default is 1)."""
        with self._lock:
            # Full-name trie insert
            node = self.root
            word = normalize(item.name)
            for ch in word:
                node = node.children.setdefault(ch, TrieNode())
            node.is_end_of_word = True
            node.weight += weight
            node.value = item  # Store the whole object
            return node
    
    def delete(self, item: object):
        """
        Deletes a word from the trie.
        Args:
            name (str): The word to be deleted from the trie.
        Returns:
            None
        Notes:
            - If the word does not exist in the trie, no changes are made.
            - The deletion is performed in a thread-safe manner.
            - Internal nodes are removed only if they are no longer needed for other words.
        """
        norm = normalize(item.name)
        with self._lock:
            def _delete(node: TrieNode, word: str, depth: int = 0) -> bool:
                if depth == len(word):
                    if not node.is_end_of_word:
                        return False  # Not found
                    node.is_end_of_word = False
                    return len(node.children) == 0  # If no children, can delete this node
                ch = word[depth]
                child_node = node.children.get(ch)
                if not child_node:
                    return False  # Not found
                should_delete_child = _delete(child_node, word, depth + 1)
                if should_delete_child:
                    del node.children[ch]
                    return not node.children and not node.is_end_of_word
                return False
            node = self.root
            for ch in norm:
                if ch not in node.children:
                    node = None
                    break
                node = node.children[ch]
            _delete(self.root, norm)

    def rename(self, old_item: object, new_item: object):
        """Rename an ingredient by removing old name and inserting new summary.

        Args:
            old_item: original ingredient name
            new_item: new ingredient summary (with updated name)
        """
        with self._lock:
            self.delete(old_item)
            self.insert(new_item)

    def prefix_search(self, prefix: str) -> List[object]:
        """Returns a list of ingredients whose name starts with the given prefix."""
        norm = normalize(prefix)
        if not norm:
            return []
        with self._lock:
            node = self.root
            try:
                for depth, ch in enumerate(norm):
                    if depth >= self.max_trie_depth:
                        logger.debug("prefix_search: depth limit reached")
                        break
                    if ch not in node.children:
                        logger.debug(f"prefix_search: miss at char '{ch}' for prefix '{norm}'")
                        return []
                    node = node.children[ch]
            except Exception as e:
                logger.error(f"Error in prefix_search traversal: {e}")
                return []
            results: List[object] = []
            self._dfs(node, norm, results)
            return results

    def _dfs(self, node: TrieNode, prefix: str, results: List[object]):
        """
        Performs a depth-first search (DFS) traversal on the Trie starting from the given node,
        collecting all values corresponding to words that begin with the specified prefix.
        Args:
            node (TrieNode): The current node in the Trie.
            prefix (str): The current prefix formed during traversal.
            results (List): The list to store values of words found during traversal.
        Returns:
            None: Results are appended to the provided results list.
        """
        
        if node.is_end_of_word and node.value is not None:
            results.append(node.value)
        for ch, child in node.children.items():
            self._dfs(child, prefix + ch, results)

    def _iterative_fuzzy(self, word: str, max_distance: int) -> List[Dict]:
        """Iterative fuzzy traversal (Levenshtein) with depth bound & row cache.

        Returns list of dicts: {"node": TrieNode, "distance": int}
        """
        results: List[Dict] = []
        initial_row = list(range(len(word) + 1))
        # Stack: (node, prefix, prev_row, depth)
        stack: List[tuple[TrieNode, str, List[int], int]] = [(self.root, "", initial_row, 0)]
        row_cache: Dict[str, List[int]] = {}
        columns = len(word) + 1
        while stack:
            node, prefix, prev_row, depth = stack.pop()
            if depth > self.max_trie_depth:
                continue
            if node.is_end_of_word and node.value is not None:
                dist = prev_row[-1]
                if dist <= max_distance:
                    results.append({"node": node, "distance": dist})
            for char, child in node.children.items():
                next_prefix = prefix + char
                cached = row_cache.get(next_prefix)
                if cached is not None:
                    current_row = cached
                else:
                    current_row = [prev_row[0] + 1]
                    for col in range(1, columns):
                        insert_cost = current_row[col - 1] + 1
                        delete_cost = prev_row[col] + 1
                        replace_cost = prev_row[col - 1] + (word[col - 1] != char)
                        current_row.append(min(insert_cost, delete_cost, replace_cost))
                    row_cache[next_prefix] = current_row
                if min(current_row) <= max_distance:
                    stack.append((child, next_prefix, current_row, depth + 1))
        return results
    
    def fuzzy_search(self, word: str, max_distance: int = 1) -> List[object]:
        """
        Performs a fuzzy search for the given word within the data structure, returning all words
        that are within the specified maximum edit distance.
        Args:
            word (str): The target word to search for.
            max_distance (int, optional): The maximum allowed edit distance for matches. Defaults to 1.
        Returns:
            list: A list of words from the data structure that match the target word within the given edit distance.
        """
        norm = normalize(word)
        if not norm:
            return []
        with self._lock:
            raw = self._iterative_fuzzy(norm, max_distance)
            ordered = sorted(
                raw,
                key=lambda x: (x["distance"] * self.distance_weight, -x["node"].weight)
            )
            return [item["node"].value for item in ordered]

class TokenSearchTrie(GenericTrieInterface):
    def __init__(self,max_trie_depth: int = 64, usage_weight: float = 0.8, distance_weight: float = 1.0):
        super().__init__()
        self.root = TokenTrieNode()  # token-level index
        self._by_id: Dict[int, object] = {}  # Mapping id -> object for token lookup resolution
        self.usage_weight = usage_weight  # Scoring weights (can be tuned externally)
        self.distance_weight = distance_weight  # multiplier for distance in ordering
        self.max_trie_depth = max_trie_depth   # Traversal guard

    def insert(self, item: object, weight: int = 1):
        with self._lock:
            # Full-name trie insert
            node = self.root
            word = normalize(item.name)
            #node.value = item  # Store the whole object
            self._by_id[item.id] = item
            # Token trie insert
            for token in filter(None, word.split()):
                node = self.root
                for ch in token:
                    node = node.children.setdefault(ch, TokenTrieNode())
                node.is_end_of_word = True
                node.items.add(item.id)
            node.weight += weight
            #item.usage_count = node.weight
            return node

    def delete(self, item: object):
        """Recursively deletes all tokens of a given item from the token trie.
        Removes empty nodes to keep the structure clean."""
        norm = normalize(item.name)
        with self._lock:
            # Find the ingredient ID (from main trie, optional)
            victim_id = None
            node = self.root
            for ch in norm:
                if ch not in node.children:
                    node = None
                    break
                node = node.children[ch]
            if node and node.is_end_of_word and node.value is not None:
                victim_id = getattr(node.value, "id", None)

            # Delete each token recursively
            for token in filter(None, norm.split()):
                self._delete_token(self.root, token, 0, victim_id)

    def _delete_token(self, node:TokenTrieNode, token: str, depth: int, victim_id: int | None) -> bool:
        """
        Recursive helper that deletes a token path.
        Returns True if the current node should be pruned.
        """
        # Base case — reached the end of the token
        if depth == len(token):
            if node.is_end_of_word:
                if victim_id is not None and victim_id in node.items:
                    node.items.discard(victim_id)
                if not node.items:
                    node.is_end_of_word = False
            # Return True if this node has no items and no children
            return not node.children and not node.items and not node.is_end_of_word

        ch = token[depth]
        child = node.children.get(ch)
        if not child:
            return False

        # Recurse deeper
        should_delete_child = self._delete_token(child, token, depth + 1, victim_id)

        # If the child is empty after recursion, remove it
        if should_delete_child:
            del node.children[ch]

        # Return True if this node is now also empty
        return not node.children and not node.items and not node.is_end_of_word

    def rename(self, old_item: object, new_item: object):
        """Rename an ingredient by removing old item and inserting new summary.

        Args:
            old_item: original ingredient item
            new_item: new ingredient summary (with updated name)
        """
        with self._lock:
            self.delete(old_item)
            self.insert(new_item)

    def _dfs(self, node: TokenTrieNode, prefix: str, results: List[Tuple[str, Set[int]]]):
        """Depth-first traversal from a given node, collecting tokens and associated ingredient IDs.
            Stops when limit is reached."""
        if node.is_end_of_word and node.items:
            results.append((prefix, node.items.copy()))

        for ch, child in node.children.items():
            self._dfs(child, prefix + ch, results)     
    
    def prefix_search(self, prefix: str) -> List[object]:
        """Performs prefix search across all tokens in the trie.
            Returns ingredient objects whose tokens start with the given prefix."""
        norm_prefix = normalize(prefix)
        results: List[Tuple[str, Set[int]]] = []
        node = self.root

        # Traverse down to the node representing the prefix
        for ch in norm_prefix:
            if ch not in node.children:
                return []  # no match
            node = node.children[ch]

        # Collect tokens and associated ingredient IDs
        self._dfs(node, norm_prefix, results)

        # Deduplicate ingredient IDs (tokens might map to same ingredient)
        found_ids: Set[int] = set()
        found_objects: List[object] = []
        for _, ids in results:
            for i in ids:
                if i not in found_ids:
                    found_ids.add(i)
                    obj = self._by_id.get(i)
                    if obj:
                        found_objects.append(obj)

        return found_objects
    
    def multi_token_prefix_search(self, query: str) -> List[object]:
        """Multi-token prefix search — all tokens in the query must match as prefixes
            in some ingredient tokens (not necessarily in order)."""
        tokens = [t for t in normalize(query).split() if t]
        if not tokens:
            return []

        with self._lock:
            candidate_sets = []
            for token in tokens:
                token_matches = {obj.id for obj in self.prefix_search(token)}
                candidate_sets.append(token_matches)
                if not token_matches:
                    return []

            # Intersection — all tokens must be found
            common_ids = set.intersection(*candidate_sets)
            return [self._by_id[i] for i in common_ids if i in self._by_id]
    
    # ---------------- Token-level fuzzy search -----------------
    def _token_iterative_fuzzy(self, token: str, max_distance: int, per_token_limit: int) -> List[Tuple[str, Set[int], int]]:
        """Fuzzy search a single token against token trie; returns (matched_token, items, distance)."""
        results: List[Tuple[str, Set[int], int]] = []
        initial_row = list(range(len(token) + 1))
        stack: List[tuple[TokenTrieNode, str, List[int], int]] = [(self.root, "", initial_row, 0)]
        columns = len(token) + 1
        while stack and len(results) < per_token_limit:
            node, prefix, prev_row, depth = stack.pop()
            if depth > self.max_trie_depth:
                continue
            if node.is_end_of_word and node.items:
                dist = prev_row[-1]
                if dist <= max_distance:
                    results.append((prefix, node.items.copy(), dist))
            for char, child in node.children.items():
                current_row = [prev_row[0] + 1]
                for col in range(1, columns):
                    insert_cost = current_row[col - 1] + 1
                    delete_cost = prev_row[col] + 1
                    replace_cost = prev_row[col - 1] + (token[col - 1] != char)
                    current_row.append(min(insert_cost, delete_cost, replace_cost))
                if min(current_row) <= max_distance:
                    stack.append((child, prefix + char, current_row, depth + 1))
        return results

    def fuzzy_search(self, query: str, token_max_distance: int = 2) -> List[object]:
        """Match multi-word queries allowing missing words in candidate or query.

        Strategy:
          * Split query into tokens (normalized)
          * For each query token perform token fuzzy search
          * Aggregate ingredient scores based on:
              - matched token count
              - sum of distances
              - usage weight
          * Allow one missing query token (flexible middle omission)
        """
        norm_query = normalize(query)
        query_tokens = [t for t in norm_query.split() if t]
        with self._lock:
            ingredient_stats: Dict[int, Dict[str, float]] = {}
            for qt in query_tokens:
                matches = self._token_iterative_fuzzy(qt, token_max_distance, per_token_limit=200)
                for matched_token, items, dist in matches:
                    for ing_id in items:
                        ing_obj = self._by_id.get(ing_id)
                        if not ing_obj:
                            continue
                        data = ingredient_stats.setdefault(ing_id, {"obj": ing_obj, "tokens": 0, "distance_sum": 0.0})
                        data["tokens"] += 1
                        data["distance_sum"] += dist
            # Scoring & filtering
            needed = max(1, len(query_tokens) - 1)  # allow one miss
            scored: List[Tuple[float, object]] = []
            for rec in ingredient_stats.values():
                matched_tokens = rec["tokens"]
                if matched_tokens < needed:
                    continue
                ing: object = rec["obj"]
                coverage = matched_tokens / len(query_tokens)
                avg_distance = rec["distance_sum"] / matched_tokens if matched_tokens else 99
                # Base score: coverage heavy, penalize distance, add usage
                score = (coverage * 3.0) - (avg_distance * self.distance_weight) + (ing.usage_count * self.usage_weight * 0.5)
                scored.append((score, ing))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [ing for _, ing in scored]

class ObjectSearchTrie:
    def __init__(self, max_trie_depth: int = 64, usage_weight: float = 0.8, prefix_boost_weight: float = 0.2, distance_weight: float = 1.0):
        self.prefix_trie = SearchTrie(max_trie_depth, distance_weight)
        self.token_trie = TokenSearchTrie(max_trie_depth, usage_weight, distance_weight)
        self.usage_weight = usage_weight  # Scoring weights (can be tuned externally)
        self.prefix_boost_weight = prefix_boost_weight
        self.distance_weight = distance_weight  # multiplier for distance in ordering

    def insert(self, item: object, weight = 1):
        prefix_node = self.prefix_trie.insert(item, weight)
        token_node = self.token_trie.insert(item, weight)
        item.usage_count = max(prefix_node.weight,token_node.weight)
    
    def delete(self, item: object):
        self.prefix_trie.delete(item)
        self.token_trie.delete(item)

    def rename(self, old_item: object, new_item: object):
        self.prefix_trie.rename(old_item, new_item)
        self.token_trie.rename(old_item, new_item)

    def prefix_search(self, prefix: str, limit: int = 50) -> List[object]:
        results = self.prefix_trie.prefix_search(prefix)
        ranked = self._rank_results(results, normalize(prefix))
        return ranked[:limit]
    
    def multi_token_prefix_search(self, query: str,limit: int = 50) -> List[object]:
        query_tokens = [t for t in query.split() if t]
        if len(query_tokens) <= 1:
            return self.prefix_trie.prefix_search(query_tokens[0] if query_tokens else query_tokens)
        results = self.token_trie.multi_token_prefix_search(query)
        ranked = self._rank_results(results, normalize(query))
        return ranked[:limit]
    
    def fuzzy_search(self, word: str, max_distance: int = 1, limit: int = 50) -> List[object]:
        results = self.prefix_trie.fuzzy_search(word, max_distance)
        return results[:limit]
    
    def multi_token_fuzzy_search(self, query: str, limit: int = 50, token_max_distance: int = 2) -> List[object]:
        query_tokens = [t for t in query.split() if t]
        if len(query_tokens) <= 1:
            return self.prefix_trie.fuzzy_search(query_tokens[0] if query_tokens else query_tokens,token_max_distance)[:limit]
        result = self.token_trie.fuzzy_search(query, token_max_distance)
        return result[:limit]
    
    def smart_search(self, query, max_distance=2, limit=50):
        norm = normalize(query)
        prefix_results = self.multi_token_prefix_search(norm, limit)
        token_results = []

        if len(prefix_results) < limit:
            token_results = self.multi_token_fuzzy_search(norm, limit=limit, token_max_distance=max_distance)

        combined = {r.id: r for r in (*prefix_results, *token_results)}
        ranked = self._rank_results(list(combined.values()), norm)
        return ranked[:limit]

    def _rank_results(self, results: List[object], query: str) -> List[object]:
        qlen = len(query)
        def score(item: object) -> float:
            name = normalize(item.name)
            prefix_bonus = 1.5 if name.startswith(query) else 1.0
            length_penalty = abs(len(name) - qlen) * 0.05
            return (item.usage_count * self.usage_weight +
                    prefix_bonus * self.prefix_boost_weight -
                    length_penalty)
        return sorted(results, key=score, reverse=True)
    
    def increment_usage(self, item: object):
        self.prefix_trie.increment_usage(item)
        self.token_trie.increment_usage(item)

    def get_depth(self) -> int:
        return max(self.prefix_trie.get_depth(), self.token_trie.get_depth())
    
    def print_tree(self):
        self.prefix_trie.print_tree_inlog_file()
        self.token_trie.print_tree_inlog_file()