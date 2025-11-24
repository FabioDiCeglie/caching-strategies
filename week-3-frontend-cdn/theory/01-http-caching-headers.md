# HTTP Caching Headers

HTTP caching headers control how browsers and CDNs cache responses. They're the foundation of frontend performance optimization.

## Why HTTP Caching Matters

Every HTTP request has cost:
- **Network latency** - Round trip to server
- **Server processing** - CPU/database time
- **Bandwidth** - Data transfer costs

HTTP caching eliminates these costs by reusing previous responses.

---

## Cache-Control Header

The primary mechanism for controlling cache behavior.

### Basic Directives

**`max-age`** - How long to cache (in seconds)
```http
Cache-Control: max-age=3600
```
Browser caches for 1 hour. No server request during this time.

**`no-cache`** - Always validate with server
```http
Cache-Control: no-cache
```
Browser must check with server before using cached version (sends ETag/Last-Modified).

**`no-store`** - Never cache
```http
Cache-Control: no-store
```
Don't cache at all. Used for sensitive data.

**`public`** - Any cache can store (browser, CDN, proxy)
```http
Cache-Control: public, max-age=31536000
```
Good for static assets (CSS, JS, images).

**`private`** - Only browser can cache (not CDN)
```http
Cache-Control: private, max-age=3600
```
Good for user-specific data (profile, settings).

### Common Patterns

**Static Assets (images, CSS, JS):**
```http
Cache-Control: public, max-age=31536000, immutable
```
Cache for 1 year. Use fingerprinted filenames for cache busting.

**API Responses (somewhat dynamic):**
```http
Cache-Control: public, max-age=60, s-maxage=300
```
Browser caches 60s, CDN caches 5min.

**User-Specific Data:**
```http
Cache-Control: private, max-age=300
```
Only browser caches, for 5 minutes.

**Real-time Data:**
```http
Cache-Control: no-cache
```
Always validate freshness.

**Sensitive Data:**
```http
Cache-Control: no-store, no-cache, must-revalidate
```
Never cache (passwords, tokens, payment info).

---

## ETag (Entity Tag)

A unique identifier for a specific version of a resource.

### How It Works

**1. Server sends ETag with response:**
```http
HTTP/1.1 200 OK
ETag: "abc123xyz"
Cache-Control: no-cache
Content-Type: application/json

{"data": "..."}
```

**2. Browser stores response + ETag**

**3. Next request includes ETag:**
```http
GET /api/data HTTP/1.1
If-None-Match: "abc123xyz"
```

**4. Server compares:**
- **If same:** Returns `304 Not Modified` (no body, saves bandwidth)
- **If changed:** Returns `200 OK` with new data + new ETag

### When to Use

✅ **Use ETag when:**
- Data changes unpredictably
- You want to validate freshness
- Bandwidth matters (304 responses are small)

❌ **Skip ETag when:**
- Using long `max-age` (no validation needed)
- Data changes very frequently
- Generating ETag is expensive

### Generating ETags

**Simple hash:**
```python
import hashlib
import json

data = {"user": "John", "posts": [1, 2, 3]}
etag = hashlib.md5(json.dumps(data).encode()).hexdigest()
# etag = "5d41402abc4b2a76b9719d911017c592"
```

**Timestamp-based:**
```python
from datetime import datetime

last_modified = datetime.utcnow()
etag = f'"{int(last_modified.timestamp())}"'
# etag = "1700000000"
```

**Database version:**
```sql
SELECT md5(string_agg(updated_at::text, '')) as etag FROM posts;
```

---

## Last-Modified Header

Alternative to ETag using timestamps.

### How It Works

**1. Server sends Last-Modified:**
```http
HTTP/1.1 200 OK
Last-Modified: Wed, 21 Oct 2024 07:28:00 GMT
Cache-Control: no-cache

{"data": "..."}
```

**2. Next request includes If-Modified-Since:**
```http
GET /api/data HTTP/1.1
If-Modified-Since: Wed, 21 Oct 2024 07:28:00 GMT
```

**3. Server compares:**
- **If not modified:** Returns `304 Not Modified`
- **If modified:** Returns `200 OK` with new data

### ETag vs Last-Modified

| Feature | ETag | Last-Modified |
|---------|------|---------------|
| Precision | Any change detected | 1-second precision |
| Generation | Content hash (CPU) | Timestamp (cheap) |
| Flexibility | Can use version numbers | Only timestamps |
| Best for | Frequently changing | Timestamped resources |

**Recommendation:** Use both! Browsers prefer ETag if both exist.

---

## Expires Header

Legacy alternative to `Cache-Control: max-age`.

```http
Expires: Wed, 21 Oct 2024 07:28:00 GMT
```

**Don't use this.** Use `Cache-Control: max-age` instead. It's simpler and more flexible.

---

## Vary Header

Tells caches which request headers affect the response.

```http
Vary: Accept-Encoding
```
Cache separately for gzip/brotli compression.

```http
Vary: Accept-Language
```
Cache separately per language.

```http
Vary: Cookie
```
Don't cache if cookies differ (user-specific content).

**Common mistake:** `Vary: *` disables all caching. Avoid!

---

## Real-World Examples

### Blog Post (changes occasionally)

**Server response:**
```http
HTTP/1.1 200 OK
Cache-Control: public, max-age=300, must-revalidate
ETag: "post-123-v5"
Last-Modified: Wed, 21 Oct 2024 07:28:00 GMT
```
- Cache 5min
- Then validate with ETag/Last-Modified
- CDN and browser can both cache

### User Profile (private, changes frequently)

**Server response:**
```http
HTTP/1.1 200 OK
Cache-Control: private, max-age=60, must-revalidate
ETag: "user-456-v12"
```
- Only browser caches (private)
- Cache 60s
- Then validate with ETag

### Static JS Bundle (immutable)

**Server response:**
```http
HTTP/1.1 200 OK
Cache-Control: public, max-age=31536000, immutable
```
- Cache 1 year
- Filename includes hash: `app.a3f2c1.js`
- If code changes → new filename → cache bypassed

### API with Real-time Data

**Server response:**
```http
HTTP/1.1 200 OK
Cache-Control: no-cache, must-revalidate
ETag: "data-v789"
```
- Must validate every time
- 304 if unchanged (saves bandwidth)
- Always fresh data

---

## Testing Cache Headers

### Chrome DevTools

1. Open **Network** tab
2. Refresh page
3. Look at **Size** column:
   - `(disk cache)` - Loaded from browser cache
   - `(memory cache)` - Loaded from RAM
   - `304 Not Modified` - Validated, still fresh
   - `200 OK` - Fresh download

4. Check **Response Headers** for:
   - `Cache-Control`
   - `ETag`
   - `Last-Modified`

### cURL

```bash
# First request
curl -I https://example.com/api/data
# Look for Cache-Control, ETag, Last-Modified

# Conditional request with ETag
curl -I -H 'If-None-Match: "abc123"' https://example.com/api/data
# Should return 304 if unchanged

# Conditional request with timestamp
curl -I -H 'If-Modified-Since: Wed, 21 Oct 2024 07:28:00 GMT' https://example.com/api/data
```

---

## Key Takeaways

✅ **Use Cache-Control** - Modern, flexible, well-supported

✅ **Set max-age** - Define explicit cache duration

✅ **Add ETag or Last-Modified** - Enable validation (304 responses)

✅ **Use public for static assets** - Allow CDN caching

✅ **Use private for user data** - Browser-only caching

✅ **Combine strategies** - `max-age` + ETag for best results

❌ **Don't use no-store everywhere** - Performance killer

❌ **Don't skip cache headers** - Browsers cache unpredictably

❌ **Don't use Expires** - Use Cache-Control instead

---

## What's Next?

Now you understand **server-side cache control**. Next, we'll explore **client-side caching** with localStorage and sessionStorage for even faster experiences.

