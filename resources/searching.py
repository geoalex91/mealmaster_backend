from __future__ import annotations
from typing import Dict, List
import threading
import unicodedata
from collections import defaultdict
from routers.schemas import IngredientsSummary

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
        c for c in normalized if unicodedata.category(c) != 'Mn'
    )
    # Convert to lowercase
    return without_diacritics.lower()
   
class TrieNode:
    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.is_end_of_word: bool = False
        self.value = None
        #self.popularity = defaultdict(int)
        self.weight = 0

class IngredientSearch:
    def __init__(self):
        self.root = TrieNode()
        self._lock = threading.Lock()
    
    def insert(self, ingredient: IngredientsSummary, weight: int = 1):
        with self._lock:
            node = self.root
            word = normalize(ingredient.name)
            for ch in word:
                node = node.children.setdefault(ch, TrieNode())
            node.is_end_of_word = True
            #node.popularity[ingredient.id] += weight
            node.weight += weight
            node.value = ingredient  # Store the whole object
            ingredient.usage_count = node.weight
    
    def delete(self, name: str):
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

        with self._lock:
            def _delete(node: TrieNode, name: str, depth: int = 0) -> bool:
                if depth == len(name):
                    if not node.is_end_of_word:
                        return False  # Not found
                    node.is_end_of_word = False
                    return len(node.children) == 0  # If no children, can delete this node
                ch = name[depth].lower()
                child_node = node.children.get(ch)
                if not child_node:
                    return False  # Not found
                should_delete_child = _delete(child_node, name, depth + 1)
                if should_delete_child:
                    del node.children[ch]
                    return not node.children and not node.is_end_of_word
                return False
            _delete(self.root, name)

    def rename(self, old_name: str, new_name: IngredientsSummary):
        with self._lock:
            self.delete(old_name)
            self.insert(new_name)

    def prefix_search(self, prefix: str, limit = 50) -> List[IngredientsSummary]:
        with self._lock:
            node = self.root
            for ch in prefix.lower():
                if ch not in node.children:
                    return []
                node = node.children[ch]
            results = []
            self._dfs(node, results, prefix,results)
            #ranked = sorted(results, key=lambda x : node.popularity.get(x.id, 0), reverse=True)
            ranked = self._rank_results(self, results, prefix)
            return ranked[:limit]

    def _dfs(self, node: TrieNode, prefix: str, results: List):
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
        
        if node.is_end_of_word:
            results.append(node.value)
        for ch, child in node.children.items():
            self._dfs(child, prefix + ch, results)

    def _fuzzy_dfs(self, node, prefix, word, prev_row, max_distance, results:List):
        """
        Performs a recursive fuzzy depth-first search (DFS) on a trie node to find words within a specified edit distance from the target word.
        Args:
            node: The current trie node being explored.
            prefix (str): The current prefix formed from traversing the trie.
            word (str): The target word to compare against.
            prev_row (list[int]): The previous row of the dynamic programming matrix representing edit distances.
            max_distance (int): The maximum allowed edit distance for a word to be considered a match.
            results (list[str]): A list to collect words from the trie that are within the allowed edit distance.
        Returns:
            None. The results are accumulated in the `results` list.
        """
        
        columns = len(word) + 1
        for char, child in node.children.items():
            current_row = [prev_row[0] + 1]
            for col in range(1, columns):
                insert_cost = current_row[col - 1] + 1
                delete_cost = prev_row[col] + 1
                replace_cost = prev_row[col - 1]
                if word[col - 1] != char:
                    replace_cost += 1
                current_row.append(min(insert_cost, delete_cost, replace_cost))
            distance = current_row[-1]
            if distance <= max_distance and child.is_end_of_word:
                results.append({"node": child, "distance": distance})
            if min(current_row) <= max_distance:
                self._fuzzy_dfs(child, prefix + char, word, current_row, max_distance, results)

    def fuzzy_search(self, word: str, max_distance: int = 1, limit = 50) -> List[IngredientsSummary]:
        """
        Performs a fuzzy search for the given word within the data structure, returning all words
        that are within the specified maximum edit distance.
        Args:
            word (str): The target word to search for.
            max_distance (int, optional): The maximum allowed edit distance for matches. Defaults to 1.
        Returns:
            list: A list of words from the data structure that match the target word within the given edit distance.
        """
        word = normalize(word)
        with self._lock:
            results = []
            initial_row = list(range(len(word) + 1))
            self._fuzzy_dfs(self.root, "", word, initial_row, max_distance, results)
            results = sorted(results, key=lambda x: (x["distance"], -x["node"].weight))
            results = [item["node"].value for item in results][:limit]
            return results
 
    def _rank_results(self, results, query):
        def score(item):
            name = normalize(item.name)
            prefix_match = 1.0 if name.startswith(query) else 0.5
            return item.usage_count * 0.8 + prefix_match * 0.2
        return sorted(results, key=score, reverse=True)

    def smart_search(self, query: str, limit: int = 50):
        """Hybrid prefix + fuzzy search with ranking."""
        prefix_results = self.prefix_search(query, limit)
        if len(prefix_results) >= limit:
            return prefix_results

        fuzzy_results = self.fuzzy_search(query, max_distance=1, limit=limit)
        
        combined = {r.id: r for r in prefix_results}
        for r in fuzzy_results:
            combined.setdefault(r.id, r)

        ranked = self.rank_results(list(combined.values()), normalize(query))
        return ranked[:limit]
    
    def increment_usage(self, ingredient: IngredientsSummary):
        node = self.root
        for ch in ingredient.name.lower():
            if ch not in node.children:
                return
            node = node.children[ch]
        if node.is_end_of_word:
            node.weight += 1
            node.value.usage_count = node.weight
            