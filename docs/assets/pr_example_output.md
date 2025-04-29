# Example SWE-agent PR Output

This is an example of a pull request created by SWE-agent through its GitHub PR integration feature.

## Pull Request Title
SWE-agent[bot] PR to fix: Fix memory leak in cache manager

## Pull Request Body

```markdown
This is a PR opened by AI tool [SWE Agent](https://github.com/SWE-agent/SWE-agent/) 
to close [#123](https://github.com/example/repo/issues/123) (Fix memory leak in cache manager).

Closes #123.

<details>
<summary>Thought process ('trajectory') of SWE-agent (click to expand)</summary>

**🧑‍🚒 Response (0)**: 
I'll examine the issue and the codebase to understand the memory leak in the cache manager.

**👀‍ Observation (0)**:
```
Looking at the repository structure...
Found the cache manager code in src/cache/manager.py
```

**🧑‍🚒 Response (1)**: 
Let me analyze the cache manager implementation to identify potential memory leaks.

**👀‍ Observation (1)**:
```
Found the following code in manager.py:

class CacheManager:
    def __init__(self):
        self._cache = {}
        
    def add(self, key, value):
        self._cache[key] = value
        
    def get(self, key):
        return self._cache.get(key)
        
    # No method to remove old entries or limit size
```

**🧑‍🚒 Response (2)**: 
I've identified the issue. The cache manager doesn't have any mechanism to remove old entries or limit its size, which can cause memory leaks as the cache grows indefinitely. I'll add a size limit and an LRU eviction policy.

**👀‍ Observation (2)**:
```
Making changes to implement LRU cache with size limit...
```

**🧑‍🚒 Response (3)**: 
I'll update the cache manager to use Python's built-in OrderedDict to implement an LRU cache with a maximum size.

**👀‍ Observation (3)**:
```
Changes made:
- Imported collections.OrderedDict
- Added max_size parameter to __init__
- Modified add method to evict oldest items when cache is full
- Added move_to_end call in get method to update LRU order
```

**🧑‍🚒 Response (4)**: 
Let me test the changes to ensure they work correctly.

**👀‍ Observation (4)**:
```
Running tests...
All tests pass.
```

**🧑‍🚒 Response (5)**: 
The fix is complete. I've implemented an LRU cache with a configurable size limit that will prevent memory leaks by evicting the least recently used items when the cache reaches its capacity.

**👀‍ Observation (5)**:
```
Changes look good. Submitting the solution.
```

</details>
```

## Branch Name
`swe-agent-fix-#123-12345678`

## Commit Message
```
Fix: Fix memory leak in cache manager
Closes #123
```