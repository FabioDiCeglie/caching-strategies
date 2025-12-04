# Next.js ISR + CDN Caching Demo

Minimal demo showing ISR (Incremental Static Regeneration) and CDN caching with Cache-Control headers.

## 🚀 Live Demo

**https://nextjs-cache-test-five.vercel.app/**

## Quick Start

```bash
npm install
npm run dev
```

Open http://localhost:3000

---

## What This Demonstrates

### 1️⃣ ISR (Incremental Static Regeneration)

```javascript
export async function getStaticProps() {
  return {
    props: { serverTime: new Date().toISOString() },
    revalidate: 10, // Regenerate every 10 seconds
  }
}
```

**How it works:**
- Page is static HTML (fast!)
- After 10s, next request triggers background regeneration
- User gets stale page instantly, fresh page ready for next visitor

---

### 2️⃣ API with CDN Cache Headers

```javascript
res.setHeader('Cache-Control', 'public, s-maxage=60, max-age=10')
```

**Headers explained:**
- `s-maxage=60` - CDN caches for 60 seconds
- `max-age=10` - Browser caches for 10 seconds
- `stale-while-revalidate` - Serve stale while refreshing

---

### 3️⃣ SWR (Client-Side)

```javascript
const { data } = useSWR('/api/time', fetcher, {
  refreshInterval: 5000
})
```

**Benefits:**
- Instant cached response
- Auto-refresh in background
- Optimistic updates

---

## Testing ISR

**Important:** ISR only works in production mode!

```bash
# Build and start production server
npm run build
npm start
```

1. Open http://localhost:3000
2. Note the "Server Time"
3. Refresh within 10 seconds → Same time (cached)
4. Wait 10+ seconds, refresh → Time updates (revalidated)

---

## Testing CDN (Deploy to Vercel)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

---

## How to Check: Browser Cache vs CDN Cache

Open DevTools → **Network** tab

### Browser Cache
Look at the **Size** column:
- `(disk cache)` or `(memory cache)` → Browser cache (no network!)
- Actual bytes (e.g., `1.2 kB`) → Network request was made

### CDN Cache (Vercel)
Click on request → **Headers** tab → Look for:
```
x-vercel-cache: HIT    → CDN served cached response ✅
x-vercel-cache: MISS   → CDN fetched from origin
x-vercel-cache: STALE  → Served stale, revalidating in background
```

### Test Flow (for /api/posts with max-age=10, s-maxage=60):

| Time | Click Refresh | Size Column | x-vercel-cache | Source |
|------|--------------|-------------|----------------|--------|
| 0s | First click | bytes | MISS | Origin |
| 2s | Click again | (disk cache) | - | Browser |
| 15s | Click again | bytes | HIT | CDN |
| 65s | Click again | bytes | MISS | Origin |

---

## Cache Flow

```
User Request
    ↓
Browser Cache (check max-age)
    ↓ HIT? → Return instantly (no network!)
    ↓ MISS/EXPIRED?
CDN Edge (check s-maxage)
    ↓ HIT? → Return cached (fast, ~10ms)
    ↓ MISS/EXPIRED?
Origin Server
    ↓
Generate Response + Cache-Control headers
    ↓
CDN stores copy (s-maxage duration)
    ↓
Browser stores copy (max-age duration)
    ↓
Return to user
```

**Example with `max-age=10, s-maxage=60`:**
- 0-10s: Browser serves (no network)
- 10-60s: CDN serves (network, but fast)
- 60s+: Origin serves (network, slower)

---

## Cache Lifecycle

| Request | Time | CDN State | What Happens | User Gets |
|---------|------|-----------|--------------|-----------|
| 1st | 0s | Empty | **Origin hit** (must!) | Fresh from origin |
| 2nd | 5s | Cached | Browser serves | Cached (no network!) |
| 3rd | 15s | Cached | CDN serves | Cached (fast) |
| 4th | 65s | Expired | CDN serves stale + background refresh | Stale (instant) |
| 5th | 66s | Refreshed | CDN serves | Fresh |

**Key insight:** First request ALWAYS hits origin (cache is empty). After that, users get cached/stale responses until cache expires.

### What is "Stale"?

- **Fresh** = Within TTL, guaranteed current
- **Stale** = Past TTL, might be slightly outdated but still usable
- **stale-while-revalidate** = Serve stale instantly, refresh in background

**Why serve stale?** Better to show slightly old data instantly than make users wait!

---

## Key Learnings

✅ **ISR** - Static speed + dynamic freshness

✅ **s-maxage** - CDN cache duration (shared cache)

✅ **max-age** - Browser cache duration (private cache)

✅ **stale-while-revalidate** - Serve stale, refresh background

✅ **SWR** - Client-side caching with auto-refresh

