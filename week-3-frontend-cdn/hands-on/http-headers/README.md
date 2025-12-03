# HTTP Caching Headers Demo

Hands-on exploration of Cache-Control, ETag, and Last-Modified headers using an interactive browser interface.

## What You'll Learn

- **Cache-Control** - Browser and CDN cache duration
- **ETag** - Content validation (304 responses save bandwidth)
- **Last-Modified** - Timestamp validation
- **public vs private** - Who can cache (CDN vs browser only)
- **304 responses** - Bandwidth savings without latency savings

---

## Quick Start

```bash
# Make scripts executable (first time)
chmod +x start.sh stop.sh

# Start
./start.sh

# Stop
./stop.sh
```

Open http://localhost:8000

**Important:** In DevTools Network tab, make sure **"Disable cache" is unchecked**!

---

## How to Use This Demo

1. Open **DevTools** (F12)
2. Go to **Network** tab
3. Uncheck "Disable cache"
4. Click buttons on the left
5. Watch the **Status**, **Size**, and **Headers** columns in Network tab
6. Key headers shown on the right side

---

## The 6 Caching Strategies

### 1️⃣ Max-Age (60 seconds)

**What it does:** Browser caches response for 60 seconds - no server request during this time.

```http
Cache-Control: public, max-age=60
```

**Test:**
- Click "Fetch Data"
- Network tab shows: `200 OK` (~538 bytes)
- Click again immediately
- Network tab shows: `(disk cache)` or `(memory cache)` - no network request!
- Wait 60+ seconds, click again
- Network tab shows: `200 OK` - cache expired

**Use for:** Content that changes occasionally (blog posts, product listings)

---

### 2️⃣ ETag Validation

**What it does:** Browser validates with server on every request. Server returns 304 if content unchanged.

```http
ETag: "abc123xyz"
Cache-Control: no-cache
```

**Test:**
- Click "Fetch Data"
- Response Headers shows: `ETag: "abc123xyz"`
- Network tab: `200 OK` (~2KB)
- Click again
- Request Headers now has: `If-None-Match: "abc123xyz"`
- Network tab: `304 Not Modified` (~200 bytes)
- **Bandwidth saved: 90%!**

**Test ETag changes:**
- Click "Add Post (Change Data)" - modifies server data
- Click "Fetch Data" again
- Network tab: `200 OK` (ETag changed! New data sent)
- ETag is a hash - when data changes, hash changes

**Use for:** Dynamic content that changes unpredictably

---

### 3️⃣ Last-Modified Validation

**What it does:** Like ETag, but uses timestamps instead of content hashes.

```http
Last-Modified: Wed, 21 Oct 2024 07:28:00 GMT
Cache-Control: no-cache
```

**Test:**
- Click "Fetch Data"
- Response Headers: `Last-Modified: [timestamp]`
- Click again
- Request Headers: `If-Modified-Since: [timestamp]`
- Network tab: `304 Not Modified`

**Use for:** Content with known update timestamps (files, documents)

---

### 4️⃣ Private Cache (User-Specific)

**What it does:** Only browser can cache, NOT CDN or proxies.

```http
Cache-Control: private, max-age=300
```

**Difference:**
- `public` → CDN + browser can cache (shared)
- `private` → Only browser caches (user-specific)

**Use for:** User profiles, account settings, dashboard data

---

### 5️⃣ No Cache (Real-time)

**What it does:** Never caches - always fetches fresh data.

```http
Cache-Control: no-cache, must-revalidate
```

**Test:**
- Click multiple times
- Every request: `200 OK`
- Notice `random_value` changes each time

**Use for:** Real-time data (stock prices, live scores, critical accuracy)

---

### 6️⃣ Static Asset (1 year)

**What it does:** Long-lived cache for files that never change.

```http
Cache-Control: public, max-age=31536000, immutable
```

**Production pattern:**
```html
<!-- ❌ Bad: cached forever, can't update -->
<script src="/app.js"></script>

<!-- ✅ Good: new version = new filename -->
<script src="/app.abc123.js"></script>
```

**Why immutable?** Browser knows file will NEVER change, skips revalidation entirely.

**Use for:** Versioned assets (CSS, JS, images with hash in filename)

---

## Strategy Comparison

| Strategy | Network Request | Bandwidth | Use Case |
|----------|----------------|-----------|----------|
| **max-age** | None (during TTL) | 0 bytes | Occasionally changing content |
| **ETag** | Validation only | 200 bytes (304) | Unpredictably changing content |
| **Last-Modified** | Validation only | 200 bytes (304) | Timestamped content |
| **private** | None (during TTL) | 0 bytes | User-specific data |
| **no-cache** | Every time | Full response | Real-time data |
| **immutable** | None (forever) | 0 bytes | Versioned static files |

---

## Key Insights

### 304 Saves Bandwidth, Not Time (for small responses)

**Bandwidth:**
- 200 OK: ~2,000 bytes
- 304 Not Modified: ~200 bytes
- **Saved: 90%**

**Time:**
- 200 OK: ~50ms
- 304: ~48ms
- **Saved: Only 2ms**

**Why?** Network round-trip still happens. 304 is critical for large files (images, videos).

**Example with 5MB image:**
- 200 OK: 500ms
- 304: 50ms
- **Saved: 450ms (90%)**

---

### ETag Auto-Detects Changes

ETag is a hash (MD5) of the content:
1. Content changes → Hash changes → ETag changes
2. Browser sends old ETag
3. Server compares → Different → Sends 200 with new data
4. Result: Always fresh data, bandwidth saved when unchanged

---

## Real-World Patterns

### Blog Post
```http
Cache-Control: public, max-age=300, must-revalidate
ETag: "post-123-v5"
```
Cache 5min, then validate. CDN and browser can both cache.

### User Profile
```http
Cache-Control: private, max-age=60
ETag: "user-456-v12"
```
Browser-only cache for 1min, then validate.

### Static JS Bundle
```http
Cache-Control: public, max-age=31536000, immutable
```
Cache 1 year. Use fingerprinted filename: `app.a3f2c1.js`

### Real-time API
```http
Cache-Control: no-cache, must-revalidate
ETag: "data-v789"
```
Always validate. 304 if unchanged (saves bandwidth).

---

## What You Learned

✅ **max-age** - Browser caches without asking server (duration-based)

✅ **ETag** - Browser asks "changed?" → 304 if not (content-based)

✅ **Last-Modified** - Browser asks "changed?" → 304 if not (time-based)

✅ **304** - Saves bandwidth (no body), but network request still happens

✅ **public** - CDN + browser can cache (shared)

✅ **private** - Only browser caches (user-specific)

✅ **immutable** - File never changes (use with versioned URLs)

---

## Next

1. **Client-side storage** - localStorage + TTL for instant access
2. **CDN caching** - Edge caching worldwide
3. **Next.js ISR** - Framework-level caching automation
