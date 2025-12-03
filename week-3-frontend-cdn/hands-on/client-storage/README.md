# Client-Side Storage Caching Demo

Interactive React demo exploring localStorage caching with TTL, Cache-First, Network-First, and SWR patterns.

## Quick Start

```bash
npm install
npm run dev
```

Open http://localhost:3000

---

## What You'll Learn

- **localStorage with TTL** - Cache expiration in the browser
- **Cache-First** - Read cache, fallback to API
- **Network-First** - Fetch fresh, fallback to cache
- **Stale-While-Revalidate (SWR)** - Instant + fresh in background

---

## The 3 Caching Strategies

### 1️⃣ Cache-First

```
1. Check cache → HIT? Return immediately (⚡ 0ms)
2. MISS? Fetch from API (~1500ms)
3. Store in cache
4. Return data
```

**Best for:** Data that doesn't change often (user profile, settings)

---

### 2️⃣ Network-First

```
1. Fetch from API first (~1500ms)
2. Store in cache
3. If API fails → Return cached data (fallback)
```

**Best for:** Data that should be fresh but needs offline support

---

### 3️⃣ Stale-While-Revalidate (SWR)

```
1. Return cached data immediately (⚡ 0ms)
2. Revalidate in background
3. Update cache for next request
```

**Best for:** Best UX - instant response + fresh data (social feeds, dashboards)

---

## How to Test

### Test Cache-First
1. Click "Fetch User (30s TTL)" → Wait ~1.5s (MISS)
2. Click again immediately → Instant! (HIT)
3. Wait 30s, click again → Wait ~1.5s (expired, MISS)

### Test SWR
1. Click "Fetch Posts (SWR)" → Wait ~1.5s (MISS)
2. Click again → Instant! Background revalidation starts
3. Check logs: "Background revalidation" message

### Inspect localStorage
1. Open DevTools → Application tab
2. Expand "Local Storage" → localhost:3000
3. See cached items with TTL metadata

---

## CacheManager API

```javascript
import { CacheManager } from './utils/CacheManager'

const cache = new CacheManager('myapp')

// Set with TTL (60 seconds)
cache.set('user', { name: 'John' }, 60)

// Get (returns { hit: true/false, value, age, remainingTtl })
const result = cache.get('user')
if (result.hit) {
  console.log(result.value) // { name: 'John' }
  console.log(result.remainingTtl) // seconds until expiry
}

// Delete
cache.delete('user')

// Clear all
cache.clear()
```

---

## Key Insights

### Why Client-Side Caching?

| Layer | Latency | When |
|-------|---------|------|
| **localStorage** | ~1ms | Instant, no network |
| **HTTP 304** | ~50ms | Network round-trip |
| **Full API call** | ~1500ms | Full request |

### When to Use Each Strategy

| Strategy | Use Case | Trade-off |
|----------|----------|-----------|
| **Cache-First** | Static data, offline | May serve stale data |
| **Network-First** | Fresh data priority | Slower, needs network |
| **SWR** | Best UX | More complex, eventual consistency |

---

## What You Learned

✅ **localStorage + TTL** - Client-side cache with expiration

✅ **Cache-First** - Fast but potentially stale

✅ **Network-First** - Fresh but slower

✅ **SWR** - Best of both (instant + background refresh)

✅ **Hit Rate** - Measure cache effectiveness

---

## Next

1. **CDN/ISR with Next.js** - Server-side caching + edge delivery

