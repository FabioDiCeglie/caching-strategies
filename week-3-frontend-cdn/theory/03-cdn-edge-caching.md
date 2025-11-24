# CDN & Edge Caching

CDNs (Content Delivery Networks) cache your content at edge servers worldwide, reducing latency and server load dramatically.

## What is a CDN?

A CDN is a network of servers distributed globally that cache your content closer to users.

**Without CDN:**
```
User (Tokyo) → Origin Server (US East) → 250ms latency
User (London) → Origin Server (US East) → 150ms latency
User (Sydney) → Origin Server (US East) → 300ms latency
```

**With CDN:**
```
User (Tokyo) → CDN Tokyo → 10ms ✅
User (London) → CDN London → 15ms ✅
User (Sydney) → CDN Sydney → 12ms ✅
```

---

## How CDN Caching Works

### Request Flow

**1. First Request (Cache MISS):**
```
User → CDN Edge → Origin Server
                  ↓
                  Response + Cache-Control
                  ↓
          CDN stores copy
          ↓
User ← CDN Edge
```

**2. Subsequent Requests (Cache HIT):**
```
User → CDN Edge → (cached, no origin request!)
        ↓
User ← Response from CDN
```

**3. After Cache Expires:**
```
User → CDN Edge → Origin (revalidate with ETag)
                  ↓
                  304 Not Modified (if unchanged)
                  ↓
          CDN extends cache
          ↓
User ← CDN Edge
```

---

## Cache-Control for CDNs

### s-maxage (Shared cache max-age)

```http
Cache-Control: max-age=60, s-maxage=3600
```

- **max-age=60** - Browser caches 1 minute
- **s-maxage=3600** - CDN caches 1 hour

Why different values?
- Users want fresh data (short browser cache)
- CDN serves millions → long cache = huge savings

### public vs private

```http
Cache-Control: public, max-age=3600
```
**public** - CDN can cache (shared cache)

```http
Cache-Control: private, max-age=3600
```
**private** - Only browser can cache (NOT CDN)

**Use private for:**
- User-specific data (profile, dashboard)
- Authenticated content
- Personalized pages

---

## CDN Providers Comparison

### Vercel Edge Network

**Best for:** Next.js, frontend apps

**Features:**
- Automatic CDN for all deployments
- Edge functions (serverless at edge)
- Zero configuration
- Generous free tier

**Cache Control:**
```javascript
// Next.js API route
export default function handler(req, res) {
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate');
  res.json({data: 'cached'});
}
```

---

### Cloudflare

**Best for:** Any website, enterprise apps

**Features:**
- 300+ edge locations
- DDoS protection
- Free tier includes CDN
- Advanced cache rules

**Cache Everything:**
```javascript
// Cloudflare Page Rule
Cache Level: Cache Everything
Edge Cache TTL: 1 hour
Browser Cache TTL: 10 minutes
```

**Purge Cache:**
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {token}" \
  -d '{"files":["https://example.com/style.css"]}'
```

---

### Netlify

**Best for:** Static sites, Jamstack

**Features:**
- Automatic CDN for static files
- Edge functions
- Deploy previews
- Git-based workflow

**Headers Configuration:**
```toml
# netlify.toml
[[headers]]
  for = "/*.js"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/api/*"
  [headers.values]
    Cache-Control = "public, max-age=60, s-maxage=300"
```

---

### AWS CloudFront

**Best for:** Enterprise, complex architectures

**Features:**
- 400+ edge locations
- Fine-grained control
- Integration with AWS services
- Pay-as-you-go pricing

**Cache Behaviors:**
- Configure TTL per path pattern
- Custom cache keys
- Origin shield for additional caching layer

---

## Edge Caching Strategies

### Static Assets (CSS, JS, Images)

```http
Cache-Control: public, max-age=31536000, immutable
```

**Why immutable?**
- Files never change (fingerprinted: `app.a3f2c1.js`)
- CDN caches forever
- New version = new filename

**Example:**
```html
<!-- Old version -->
<script src="/app.abc123.js"></script>

<!-- Deploy new code → new hash -->
<script src="/app.xyz789.js"></script>
```

---

### API Responses (Dynamic but cacheable)

```http
Cache-Control: public, max-age=60, s-maxage=300, stale-while-revalidate=600
```

**Breakdown:**
- Browser: 1 minute
- CDN: 5 minutes
- SWR: Serve stale for 10 minutes while revalidating

**Best for:**
- Product listings
- Blog posts
- Public data

---

### Personalized Content

```http
Cache-Control: private, max-age=300
Vary: Cookie
```

**CDN won't cache** due to `private` or `Vary: Cookie`.

**Alternative:** Edge personalization (Cloudflare Workers, Vercel Edge Functions)

```javascript
// Vercel Edge Function
export default function handler(req) {
  const userId = req.cookies.get('userId');
  
  // Fetch from cached global data
  const globalData = await fetch('https://api.example.com/global');
  
  // Personalize at edge (fast!)
  const personalized = {
    ...globalData,
    user: userId
  };
  
  return Response.json(personalized);
}
```

---

## Cache Invalidation (Purging)

### Time-Based (Automatic)

```http
Cache-Control: max-age=300
```
CDN automatically purges after 5 minutes.

**Pros:** Simple, no manual work  
**Cons:** Stale content for TTL duration

---

### Manual Purge (On-Demand)

**Vercel:**
```bash
# Purge all
vercel env pull
curl -X PURGE https://your-site.vercel.app

# Purge specific path
curl -X PURGE https://your-site.vercel.app/api/posts
```

**Cloudflare API:**
```javascript
// Purge specific URLs
await fetch('https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer {token}',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    files: [
      'https://example.com/api/posts',
      'https://example.com/api/posts/123'
    ]
  })
});
```

**Netlify:**
```bash
# Purge all
netlify deploy --prod

# Automatic purge on deploy
```

---

### Event-Based Invalidation

Invalidate when content changes:

```javascript
// After publishing blog post
await db.posts.create(newPost);

// Purge CDN cache
await purgeCDN([
  '/api/posts',
  `/api/posts/${newPost.id}`,
  '/'  // Homepage
]);
```

---

## Cache Tags (Advanced)

Group related URLs for bulk invalidation.

**Cloudflare example:**
```http
Cache-Tag: post-123, category-tech, author-456
```

**Purge by tag:**
```bash
# Purge all posts in "tech" category
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -d '{"tags":["category-tech"]}'
```

**Use case:**
- Publish new post → Purge `author-456` (all author's posts)
- Update category → Purge `category-tech` (all posts in category)

---

## CDN Cache vs Browser Cache

| Layer | Location | Control | Shared |
|-------|----------|---------|--------|
| Browser | User's device | `max-age` | ❌ Per user |
| CDN Edge | Datacenter near user | `s-maxage` | ✅ All users in region |
| Origin | Your server | - | - |

**Optimize both:**
```http
Cache-Control: public, max-age=60, s-maxage=3600
```
- User refreshes page → Browser serves from cache (0ms)
- Different user nearby → CDN serves (10ms)
- User far away, first request → Origin (100ms+)

---

## Real-World Performance

### Without CDN

```
Origin Server (US East)
├─ User (Tokyo): 250ms
├─ User (London): 150ms
├─ User (Sydney): 300ms
└─ Server load: 1000 req/s
```

**Problems:**
- High latency for distant users
- Server bottleneck
- Expensive bandwidth

---

### With CDN

```
CDN Tokyo (cache hit): 10ms
CDN London (cache hit): 15ms
CDN Sydney (cache hit): 12ms
Origin Server: 10 req/s (only cache misses)
```

**Benefits:**
- 95-97% cache hit rate typical
- Origin sees 3-5% of traffic
- 10-20x latency improvement
- Massive cost savings

---

## Testing CDN Caching

### Check Cache Status

Most CDNs add headers:

**Vercel:**
```http
x-vercel-cache: HIT
```

**Cloudflare:**
```http
cf-cache-status: HIT
```

**Netlify:**
```http
x-nf-request-id: ...
```

### cURL Test

```bash
# First request
curl -I https://your-site.com/api/data
# x-vercel-cache: MISS

# Second request (should be HIT)
curl -I https://your-site.com/api/data
# x-vercel-cache: HIT
```

### Chrome DevTools

1. Open Network tab
2. Look for `cf-cache-status` or `x-vercel-cache` header
3. `HIT` = served from CDN
4. `MISS` = fetched from origin

---

## CDN Best Practices

### ✅ DO

**1. Use long cache times for static assets**
```http
Cache-Control: public, max-age=31536000, immutable
```

**2. Use fingerprinted filenames**
```
app.a3f2c1.js  (not app.js)
style.xyz123.css  (not style.css)
```

**3. Set different TTLs for browser vs CDN**
```http
Cache-Control: max-age=60, s-maxage=3600
```

**4. Use stale-while-revalidate**
```http
Cache-Control: max-age=60, stale-while-revalidate=600
```

**5. Purge on deploy**
```bash
# In CI/CD pipeline
vercel deploy --prod
purgeCDN()
```

### ❌ DON'T

**1. Don't cache personalized content globally**
```http
# Bad: CDN caches, serves wrong user's data
Cache-Control: public, max-age=3600

# Good: Only browser caches
Cache-Control: private, max-age=300
```

**2. Don't use Vary: * (disables caching)**
```http
Vary: *  # DON'T DO THIS
```

**3. Don't forget to version assets**
```html
<!-- Bad: cached forever, can't update -->
<script src="/app.js"></script>

<!-- Good: new version = new URL -->
<script src="/app.v2.js"></script>
```

**4. Don't cache error responses**
```javascript
if (error) {
  res.setHeader('Cache-Control', 'no-store');
  res.status(500).json({error});
}
```

---

## Cost Savings Example

### Scenario: Blog with 1M monthly pageviews

**Without CDN:**
- 1M requests to origin
- Average 100KB per page
- Bandwidth: 100GB/month
- Server: Handle 385 req/minute (average)
- Cost: ~$200/month (server + bandwidth)

**With CDN (95% cache hit rate):**
- 50K requests to origin (5%)
- 950K requests served by CDN
- Origin bandwidth: 5GB/month
- Server: Handle 19 req/minute (average)
- Cost: ~$20/month + CDN (often free)

**Savings: 90% reduction in costs**

---

## Key Takeaways

✅ **Use CDN for all public content** - Massive performance gain

✅ **Set s-maxage higher than max-age** - Reduce origin load

✅ **Use immutable for static assets** - Cache forever with fingerprinting

✅ **Purge on deploy** - Keep content fresh

✅ **Test cache headers** - Verify HIT/MISS status

✅ **Private for user-specific data** - Prevent cache leaks

❌ **Don't cache personalized content** - Use edge functions instead

❌ **Don't skip cache headers** - CDN needs guidance

---

## What's Next?

You understand CDN caching at the edge. Next, we'll combine everything with **Next.js ISR and SWR** - the modern framework that handles caching at all levels automatically.

