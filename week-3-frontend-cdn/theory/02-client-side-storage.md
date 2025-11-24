# Client-Side Storage Caching

Client-side caching stores data in the browser itself, eliminating network requests entirely. It's the fastest form of caching.

## Why Client-Side Caching?

HTTP caching still requires validation (304 responses). Client-side caching is **instant** - no network at all.

**Performance comparison:**
- HTTP cache (disk): ~50-100ms
- HTTP 304 validation: ~20-50ms
- Client-side cache: **~0-5ms**

---

## localStorage vs sessionStorage vs Memory

### localStorage

**Persistent storage** - survives browser restarts.

```javascript
// Set
localStorage.setItem('user', JSON.stringify({id: 1, name: 'John'}));

// Get
const user = JSON.parse(localStorage.getItem('user'));

// Remove
localStorage.removeItem('user');

// Clear all
localStorage.clear();
```

**Capacity:** ~5-10MB per origin

**Use cases:**
- User preferences (theme, language)
- Draft content (unsaved form data)
- Recent searches
- Offline data

---

### sessionStorage

**Session-only storage** - cleared when tab closes.

```javascript
// Same API as localStorage
sessionStorage.setItem('cart', JSON.stringify([1, 2, 3]));
const cart = JSON.parse(sessionStorage.getItem('cart'));
```

**Capacity:** ~5-10MB per origin

**Use cases:**
- Shopping cart (current session)
- Form wizard state
- Temporary filters/selections
- Single-page app state

---

### In-Memory Cache

**Fastest but temporary** - cleared on page reload.

```javascript
const cache = new Map();

// Set
cache.set('posts', [{id: 1, title: 'Hello'}]);

// Get
const posts = cache.get('posts');

// Remove
cache.delete('posts');
```

**Capacity:** Limited by available RAM

**Use cases:**
- API response caching (during page session)
- Computed values
- Memoization
- Component state

---

## Comparison Table

| Feature | localStorage | sessionStorage | Memory |
|---------|--------------|----------------|--------|
| Persistence | Until cleared | Until tab closes | Until reload |
| Capacity | 5-10MB | 5-10MB | RAM limit |
| Speed | Fast | Fast | Fastest |
| Shared across tabs | ✅ Yes | ❌ No | ❌ No |
| Server access | ❌ No | ❌ No | ❌ No |

---

## Building a Cache with TTL

localStorage doesn't support expiration. We need to implement it ourselves.

### Basic TTL Pattern

```javascript
// Set with TTL
function setCache(key, value, ttlSeconds) {
  const item = {
    value: value,
    expiresAt: Date.now() + (ttlSeconds * 1000)
  };
  localStorage.setItem(key, JSON.stringify(item));
}

// Get with TTL check
function getCache(key) {
  const itemStr = localStorage.getItem(key);
  if (!itemStr) return null;
  
  const item = JSON.parse(itemStr);
  
  // Check expiration
  if (Date.now() > item.expiresAt) {
    localStorage.removeItem(key);
    return null;
  }
  
  return item.value;
}
```

**Usage:**
```javascript
// Cache for 5 minutes
setCache('posts', [{id: 1}, {id: 2}], 300);

// Retrieve
const posts = getCache('posts');
if (posts) {
  console.log('Cache hit!', posts);
} else {
  console.log('Cache miss - fetch from API');
}
```

---

## Cache Manager Class

More organized approach:

```javascript
class CacheManager {
  constructor(prefix = 'app') {
    this.prefix = prefix;
  }
  
  // Generate key with prefix
  _getKey(key) {
    return `${this.prefix}:${key}`;
  }
  
  // Set with TTL
  set(key, value, ttlSeconds = 300) {
    const item = {
      value: value,
      expiresAt: Date.now() + (ttlSeconds * 1000),
      cachedAt: Date.now()
    };
    
    try {
      localStorage.setItem(this._getKey(key), JSON.stringify(item));
      return true;
    } catch (e) {
      console.error('Cache set failed:', e);
      return false;
    }
  }
  
  // Get with automatic expiration check
  get(key) {
    const itemStr = localStorage.getItem(this._getKey(key));
    if (!itemStr) return null;
    
    try {
      const item = JSON.parse(itemStr);
      
      // Check expiration
      if (Date.now() > item.expiresAt) {
        this.delete(key);
        return null;
      }
      
      return item.value;
    } catch (e) {
      console.error('Cache get failed:', e);
      return null;
    }
  }
  
  // Delete single key
  delete(key) {
    localStorage.removeItem(this._getKey(key));
  }
  
  // Clear all keys with prefix
  clear() {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith(this.prefix + ':')) {
        localStorage.removeItem(key);
      }
    });
  }
  
  // Get cache info (for debugging)
  getInfo(key) {
    const itemStr = localStorage.getItem(this._getKey(key));
    if (!itemStr) return null;
    
    const item = JSON.parse(itemStr);
    const now = Date.now();
    
    return {
      cached: true,
      age: Math.floor((now - item.cachedAt) / 1000),
      ttl: Math.floor((item.expiresAt - now) / 1000),
      expired: now > item.expiresAt
    };
  }
}
```

**Usage:**
```javascript
const cache = new CacheManager('myapp');

// Set
cache.set('user:123', {name: 'John'}, 600); // 10 min

// Get
const user = cache.get('user:123');

// Check info
const info = cache.getInfo('user:123');
console.log(`Cached ${info.age}s ago, expires in ${info.ttl}s`);

// Clear all
cache.clear();
```

---

## Cache-First vs Network-First

### Cache-First (Fast but potentially stale)

```javascript
async function fetchWithCacheFirst(url, ttl = 300) {
  const cache = new CacheManager();
  
  // 1. Try cache first
  const cached = cache.get(url);
  if (cached) {
    console.log('Cache HIT');
    return cached;
  }
  
  // 2. Fetch from network
  console.log('Cache MISS - fetching...');
  const response = await fetch(url);
  const data = await response.json();
  
  // 3. Store in cache
  cache.set(url, data, ttl);
  
  return data;
}
```

**Best for:**
- Data that doesn't change often
- Offline-first apps
- Maximum performance

---

### Network-First (Fresh but slower)

```javascript
async function fetchWithNetworkFirst(url, ttl = 300) {
  const cache = new CacheManager();
  
  try {
    // 1. Try network first
    const response = await fetch(url);
    const data = await response.json();
    
    // 2. Update cache
    cache.set(url, data, ttl);
    console.log('Network SUCCESS');
    return data;
    
  } catch (error) {
    // 3. Fallback to cache if network fails
    console.log('Network FAILED - trying cache...');
    const cached = cache.get(url);
    
    if (cached) {
      console.log('Cache FALLBACK');
      return cached;
    }
    
    throw new Error('No network and no cache');
  }
}
```

**Best for:**
- Real-time data
- Critical accuracy
- Offline fallback

---

## Stale-While-Revalidate (SWR)

Best of both: instant cached response + background refresh.

```javascript
async function fetchWithSWR(url, ttl = 300) {
  const cache = new CacheManager();
  
  // 1. Get cached data (even if stale)
  const cached = cache.get(url);
  const info = cache.getInfo(url);
  
  // 2. If cache exists (fresh or stale), return it immediately
  if (cached) {
    console.log(info.expired ? 'STALE cache' : 'FRESH cache');
    
    // 3. If stale, revalidate in background
    if (info.expired) {
      console.log('Revalidating in background...');
      fetch(url)
        .then(res => res.json())
        .then(data => {
          cache.set(url, data, ttl);
          console.log('Cache revalidated');
        })
        .catch(err => console.error('Revalidation failed:', err));
    }
    
    return cached;
  }
  
  // 4. No cache - fetch normally
  console.log('No cache - fetching...');
  const response = await fetch(url);
  const data = await response.json();
  cache.set(url, data, ttl);
  return data;
}
```

**Best for:**
- News feeds, social media
- Dashboard data
- Product listings
- Any UI that needs to feel instant

---

## Cache Invalidation

### Time-Based (TTL)

Already covered - automatic expiration.

### Manual Invalidation

```javascript
// After creating a post
await fetch('/api/posts', {method: 'POST', body: newPost});
cache.delete('/api/posts'); // Invalidate list cache

// After updating user
await fetch('/api/user/123', {method: 'PUT', body: updates});
cache.delete('/api/user/123'); // Invalidate user cache
```

### Pattern-Based Invalidation

```javascript
class CacheManager {
  // ... previous methods ...
  
  deletePattern(pattern) {
    const keys = Object.keys(localStorage);
    const fullPattern = new RegExp(this.prefix + ':' + pattern);
    
    keys.forEach(key => {
      if (fullPattern.test(key)) {
        localStorage.removeItem(key);
      }
    });
  }
}

// Usage
cache.deletePattern('user:.*'); // Delete all user caches
cache.deletePattern('posts:.*'); // Delete all post caches
```

---

## Storage Quotas & Limits

### Check Storage Usage

```javascript
if ('storage' in navigator && 'estimate' in navigator.storage) {
  navigator.storage.estimate().then(estimate => {
    const usedMB = (estimate.usage / 1024 / 1024).toFixed(2);
    const totalMB = (estimate.quota / 1024 / 1024).toFixed(2);
    const percentUsed = ((estimate.usage / estimate.quota) * 100).toFixed(1);
    
    console.log(`Storage: ${usedMB}MB / ${totalMB}MB (${percentUsed}%)`);
  });
}
```

### Handle Quota Exceeded

```javascript
function safeSetCache(key, value, ttl) {
  try {
    cache.set(key, value, ttl);
    return true;
  } catch (e) {
    if (e.name === 'QuotaExceededError') {
      console.warn('Storage quota exceeded - clearing old cache');
      cache.clear();
      
      // Try again
      try {
        cache.set(key, value, ttl);
        return true;
      } catch (e2) {
        console.error('Still failed after clearing cache');
        return false;
      }
    }
    return false;
  }
}
```

---

## When NOT to Use Client-Side Caching

❌ **Sensitive data** - localStorage is NOT secure
- Passwords, tokens, payment info
- Use secure httpOnly cookies instead

❌ **Large files** - localStorage has 5-10MB limit
- Videos, large images
- Use IndexedDB or server-side storage

❌ **Cross-tab synchronization critical**
- sessionStorage doesn't sync
- Use localStorage + storage events or server

❌ **SEO-critical content**
- Search engines can't see cached content
- Use SSR/SSG instead

---

## Real-World Examples

### Blog Post List

```javascript
// Fast load with stale-while-revalidate
const posts = await fetchWithSWR('/api/posts', 60);
```

### User Preferences

```javascript
// Long-lived cache
cache.set('theme', 'dark', 30 * 24 * 60 * 60); // 30 days
const theme = cache.get('theme') || 'light';
```

### Search Results

```javascript
// Cache recent searches
const query = 'javascript';
const results = cache.get(`search:${query}`);

if (!results) {
  const fresh = await fetch(`/api/search?q=${query}`);
  cache.set(`search:${query}`, fresh, 300); // 5 min
}
```

### Shopping Cart (session only)

```javascript
// Use sessionStorage for temporary state
const cart = JSON.parse(sessionStorage.getItem('cart') || '[]');
cart.push({id: 123, qty: 1});
sessionStorage.setItem('cart', JSON.stringify(cart));
```

---

## Key Takeaways

✅ **Use localStorage for persistent data** (preferences, drafts)

✅ **Use sessionStorage for temporary state** (cart, filters)

✅ **Always implement TTL** - prevent stale data

✅ **Handle quota errors gracefully** - clear old cache

✅ **Invalidate on writes** - keep cache fresh

✅ **Use SWR for best UX** - instant + fresh

❌ **Never store sensitive data** - localStorage is NOT secure

❌ **Don't cache everything** - be selective

---

## What's Next?

You now understand client-side caching in the browser. Next, we'll explore **CDN and edge caching** - how content is cached globally for users worldwide.

