/**
 * Client-Side Cache Manager with TTL Support
 * Demonstrates localStorage caching with expiration
 */
export class CacheManager {
  constructor(prefix = 'cache') {
    this.prefix = prefix
  }

  _getKey(key) {
    return `${this.prefix}:${key}`
  }

  /**
   * Set a value with TTL (time-to-live in seconds)
   */
  set(key, value, ttlSeconds = 60) {
    const item = {
      value: value,
      cachedAt: Date.now(),
      expiresAt: Date.now() + (ttlSeconds * 1000),
      ttl: ttlSeconds
    }
    
    try {
      localStorage.setItem(this._getKey(key), JSON.stringify(item))
      return { success: true, key, ttl: ttlSeconds }
    } catch (e) {
      console.error('Cache set failed:', e)
      return { success: false, error: e.message }
    }
  }

  /**
   * Get a value (returns null if expired or not found)
   */
  get(key) {
    const itemStr = localStorage.getItem(this._getKey(key))
    if (!itemStr) {
      return { hit: false, reason: 'not_found' }
    }
    
    try {
      const item = JSON.parse(itemStr)
      const now = Date.now()
      
      // Check expiration
      if (now > item.expiresAt) {
        localStorage.removeItem(this._getKey(key))
        return { 
          hit: false, 
          reason: 'expired',
          age: Math.floor((now - item.cachedAt) / 1000),
          ttl: item.ttl
        }
      }
      
      return {
        hit: true,
        value: item.value,
        age: Math.floor((now - item.cachedAt) / 1000),
        remainingTtl: Math.floor((item.expiresAt - now) / 1000)
      }
    } catch (e) {
      return { hit: false, reason: 'parse_error' }
    }
  }

  /**
   * Delete a specific key
   */
  delete(key) {
    localStorage.removeItem(this._getKey(key))
    return { deleted: true, key }
  }

  /**
   * Clear all keys with this prefix
   */
  clear() {
    const keys = Object.keys(localStorage)
    let count = 0
    keys.forEach(key => {
      if (key.startsWith(this.prefix + ':')) {
        localStorage.removeItem(key)
        count++
      }
    })
    return { cleared: count }
  }

  /**
   * Get all cached items (for debugging)
   */
  getAll() {
    const keys = Object.keys(localStorage)
    const items = []
    const now = Date.now()
    
    keys.forEach(key => {
      if (key.startsWith(this.prefix + ':')) {
        try {
          const item = JSON.parse(localStorage.getItem(key))
          items.push({
            key: key.replace(this.prefix + ':', ''),
            value: item.value,
            age: Math.floor((now - item.cachedAt) / 1000),
            remainingTtl: Math.floor((item.expiresAt - now) / 1000),
            expired: now > item.expiresAt
          })
        } catch (e) {
          // Skip invalid items
        }
      }
    })
    
    return items
  }
}

/**
 * Real API calls using JSONPlaceholder (free public API)
 * These are REAL network requests - visible in Network tab!
 */
export async function fetchFromAPI(endpoint) {
  const BASE_URL = 'https://jsonplaceholder.typicode.com'
  
  switch (endpoint) {
    case '/api/user':
      const userRes = await fetch(`${BASE_URL}/users/1`)
      return await userRes.json()
      
    case '/api/posts':
      const postsRes = await fetch(`${BASE_URL}/posts?_limit=5`)
      return await postsRes.json()
      
    case '/api/settings':
      // Simulate settings with a user endpoint
      const settingsRes = await fetch(`${BASE_URL}/users/1`)
      const user = await settingsRes.json()
      return { 
        theme: 'dark', 
        language: 'en', 
        email: user.email,
        notifications: true 
      }
      
    default:
      const defaultRes = await fetch(`${BASE_URL}/posts/1`)
      return await defaultRes.json()
  }
}
