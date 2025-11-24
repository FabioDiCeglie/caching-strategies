# Next.js ISR & SWR

Next.js combines server-side rendering, static generation, and intelligent caching into one framework. ISR and SWR are game-changers for modern web apps.

## The Problem with Traditional Approaches

### Pure Static (SSG)

```javascript
// Build time only
export async function getStaticProps() {
  const posts = await fetchPosts();
  return { props: { posts } };
}
```

**Problem:** Content is stale until next build/deploy.

---

### Pure Server-Side (SSR)

```javascript
// Every request
export async function getServerSideProps() {
  const posts = await fetchPosts();
  return { props: { posts } };
}
```

**Problem:** Slow, expensive, scales poorly.

---

### Next.js Solution: ISR + SWR

**ISR (Incremental Static Regeneration)** - Static with automatic background updates  
**SWR (Stale-While-Revalidate)** - Client-side cache with background refresh

Best of both worlds: **fast + fresh**

---

## ISR (Incremental Static Regeneration)

### How It Works

```javascript
export async function getStaticProps() {
  const posts = await fetchPosts();
  
  return {
    props: { posts },
    revalidate: 60  // Revalidate every 60 seconds
  };
}
```

**Request Timeline:**

**First request (after build):**
- Serves static HTML (instant)
- Background: Check if > 60s since last generation

**If > 60s:**
- Still serves stale HTML (instant)
- Background: Regenerate page
- Next request gets fresh version

**If < 60s:**
- Serves cached HTML (instant)
- No regeneration

---

### ISR Request Flow

```
Request 1 (t=0s):
User → CDN/Vercel → Static HTML (fast!)
                    ↓
                No revalidation (< 60s since build)

Request 2 (t=70s):
User → CDN/Vercel → Static HTML (fast! still serving old)
                    ↓
                Background: Regenerate (user doesn't wait)
                    ↓
                New HTML ready

Request 3 (t=75s):
User → CDN/Vercel → New HTML (fresh!)
```

**Key insight:** Users always get instant response, never wait for regeneration.

---

### ISR Example: Blog

```javascript
// pages/posts/[id].js

export async function getStaticPaths() {
  // Only pre-render popular posts at build
  const popularPosts = await fetchPopularPosts();
  
  return {
    paths: popularPosts.map(p => ({ params: { id: p.id } })),
    fallback: 'blocking'  // Generate others on-demand
  };
}

export async function getStaticProps({ params }) {
  const post = await fetchPost(params.id);
  
  return {
    props: { post },
    revalidate: 300,  // Revalidate every 5 minutes
  };
}

export default function Post({ post }) {
  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.content}</p>
    </article>
  );
}
```

**Benefits:**
- Build time: Only 100 popular posts
- Runtime: Generate remaining posts on-demand
- All posts: Auto-update every 5 minutes if visited
- Users: Always fast (static HTML)

---

### Fallback Strategies

**fallback: false**
```javascript
return {
  paths: [...],
  fallback: false  // 404 for unknown paths
};
```
Use when: All paths known at build time

**fallback: true**
```javascript
return {
  paths: [...],
  fallback: true  // Show loading, generate in background
};

export default function Post({ post }) {
  const router = useRouter();
  
  if (router.isFallback) {
    return <div>Loading...</div>;
  }
  
  return <article>{post.title}</article>;
}
```
Use when: Many possible paths, show loading state

**fallback: 'blocking'**
```javascript
return {
  paths: [...],
  fallback: 'blocking'  // Wait for generation (SSR-like)
};
```
Use when: Better SEO (no loading state), acceptable wait time

---

## On-Demand Revalidation

Invalidate specific pages when content changes.

### Setup API Route

```javascript
// pages/api/revalidate.js

export default async function handler(req, res) {
  // Check secret to prevent unauthorized revalidation
  if (req.query.secret !== process.env.REVALIDATE_SECRET) {
    return res.status(401).json({ message: 'Invalid token' });
  }

  try {
    // Revalidate specific paths
    await res.revalidate('/');
    await res.revalidate('/posts');
    await res.revalidate(`/posts/${req.query.id}`);
    
    return res.json({ revalidated: true });
  } catch (err) {
    return res.status(500).send('Error revalidating');
  }
}
```

### Trigger from Backend

```javascript
// After publishing post in backend
await db.posts.create(newPost);

// Trigger revalidation
await fetch(`https://your-site.com/api/revalidate?secret=${SECRET}&id=${newPost.id}`);
```

**Result:** Fresh content immediately, no waiting for TTL.

---

## API Routes with Cache-Control

Next.js API routes can set cache headers like any backend.

### Example: Cached API

```javascript
// pages/api/posts.js

export default async function handler(req, res) {
  const posts = await db.posts.findAll();
  
  // Cache for 1 minute in browser, 5 minutes in CDN
  res.setHeader('Cache-Control', 'public, s-maxage=300, max-age=60');
  
  res.json(posts);
}
```

### Dynamic Cache Headers

```javascript
export default async function handler(req, res) {
  // Authenticated request - don't cache
  if (req.headers.authorization) {
    res.setHeader('Cache-Control', 'private, no-cache');
    const userData = await fetchUserData(req.userId);
    return res.json(userData);
  }
  
  // Public data - cache aggressively
  res.setHeader('Cache-Control', 'public, s-maxage=3600, stale-while-revalidate');
  const publicData = await fetchPublicData();
  res.json(publicData);
}
```

---

## SWR (useSWR Hook)

Client-side data fetching with caching, revalidation, and auto-refresh.

### Basic Usage

```javascript
import useSWR from 'swr';

const fetcher = (url) => fetch(url).then(r => r.json());

export default function Profile() {
  const { data, error, isLoading } = useSWR('/api/user', fetcher);
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading user</div>;
  
  return <div>Hello {data.name}!</div>;
}
```

**What SWR does automatically:**
1. Fetch data
2. Cache in memory
3. Revalidate on focus
4. Revalidate on reconnect
5. Interval polling (optional)

---

### SWR Configuration

```javascript
const { data, error, mutate } = useSWR('/api/posts', fetcher, {
  revalidateOnFocus: true,     // Refresh when window focused
  revalidateOnReconnect: true, // Refresh when back online
  refreshInterval: 30000,      // Poll every 30 seconds
  dedupingInterval: 5000,      // Dedupe requests within 5s
  focusThrottleInterval: 5000, // Throttle focus revalidation
});
```

---

### SWR with Optimistic Updates

```javascript
import useSWR, { mutate } from 'swr';

function Posts() {
  const { data: posts } = useSWR('/api/posts', fetcher);
  
  async function createPost(newPost) {
    // 1. Optimistically update UI
    mutate('/api/posts', [...posts, newPost], false);
    
    // 2. Send to server
    await fetch('/api/posts', {
      method: 'POST',
      body: JSON.stringify(newPost)
    });
    
    // 3. Revalidate to get server state
    mutate('/api/posts');
  }
  
  return (
    <div>
      {posts.map(post => <div key={post.id}>{post.title}</div>)}
      <button onClick={() => createPost({title: 'New'})}>
        Add Post
      </button>
    </div>
  );
}
```

**User experience:**
- Click "Add Post" → **Instant UI update**
- Background: Server request
- Revalidate: Confirm server state

---

### SWR with Conditional Fetching

```javascript
function User({ userId }) {
  // Only fetch if userId exists
  const { data } = useSWR(
    userId ? `/api/user/${userId}` : null,
    fetcher
  );
  
  if (!userId) return <div>No user selected</div>;
  if (!data) return <div>Loading...</div>;
  
  return <div>{data.name}</div>;
}
```

---

### Global SWR Configuration

```javascript
// pages/_app.js
import { SWRConfig } from 'swr';

function MyApp({ Component, pageProps }) {
  return (
    <SWRConfig
      value={{
        refreshInterval: 30000,
        fetcher: (url) => fetch(url).then(r => r.json()),
        revalidateOnFocus: true,
        dedupingInterval: 2000,
      }}
    >
      <Component {...pageProps} />
    </SWRConfig>
  );
}
```

---

## Combining ISR + SWR

Perfect combo: Fast initial load + Always fresh data.

```javascript
// pages/posts.js

// Server-side: ISR
export async function getStaticProps() {
  const posts = await fetchPosts();
  
  return {
    props: { initialPosts: posts },
    revalidate: 60  // Revalidate every minute
  };
}

// Client-side: SWR
export default function Posts({ initialPosts }) {
  const { data: posts } = useSWR('/api/posts', fetcher, {
    fallbackData: initialPosts,  // Use ISR data initially
    refreshInterval: 30000,      // Poll every 30s when tab active
  });
  
  return (
    <div>
      {posts.map(post => (
        <article key={post.id}>{post.title}</article>
      ))}
    </div>
  );
}
```

**Timeline:**
1. **Initial load:** Static HTML with `initialPosts` (instant)
2. **Client hydration:** SWR uses `initialPosts` (no flash)
3. **After 30s:** SWR fetches fresh data in background
4. **User returns later:** Gets updated HTML from ISR
5. **Tab focus:** SWR revalidates immediately

**Result:** Always fast + Always fresh

---

## Performance Comparison

### Pure SSR (No caching)

```
Every request:
- TTFB: 500ms (database query)
- FCP: 600ms
- Server load: 100%
```

### ISR

```
Cached request:
- TTFB: 20ms (static HTML)
- FCP: 100ms
- Server load: 2% (background revalidation)

Revalidation request:
- TTFB: 20ms (still serves stale)
- Background: 500ms (regenerate)
- User experience: unchanged (no wait)
```

### ISR + SWR

```
Initial:
- TTFB: 20ms (ISR)
- FCP: 100ms
- Interactive: 200ms

Client-side updates:
- Background fetch: 50ms (API route)
- UI update: instant (optimistic)
- Revalidation: automatic
```

---

## Real-World Patterns

### E-Commerce Product Page

```javascript
// Static generation with 5min revalidation
export async function getStaticProps({ params }) {
  const product = await fetchProduct(params.id);
  
  return {
    props: { product },
    revalidate: 300,  // 5 minutes
  };
}

export default function Product({ product }) {
  // Real-time inventory with SWR
  const { data: inventory } = useSWR(
    `/api/inventory/${product.id}`,
    fetcher,
    { refreshInterval: 10000 }  // Update every 10s
  );
  
  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <p>In stock: {inventory?.count || product.inventory}</p>
    </div>
  );
}
```

**Benefits:**
- Product details: Fast static page
- Inventory: Real-time updates
- SEO: Perfect (static HTML)

---

### Social Media Feed

```javascript
export async function getServerSideProps() {
  // Initial posts for SEO
  const initialPosts = await fetchPosts({ limit: 20 });
  
  return { props: { initialPosts } };
}

export default function Feed({ initialPosts }) {
  const [page, setPage] = useState(1);
  
  // Paginated SWR
  const { data: posts } = useSWR(
    `/api/posts?page=${page}`,
    fetcher,
    {
      fallbackData: page === 1 ? initialPosts : undefined,
      refreshInterval: 15000,  // Auto-refresh every 15s
    }
  );
  
  return (
    <div>
      {posts.map(post => <Post key={post.id} {...post} />)}
      <button onClick={() => setPage(p => p + 1)}>Load More</button>
    </div>
  );
}
```

---

### News/Blog Site

```javascript
// Homepage with ISR
export async function getStaticProps() {
  const posts = await fetchRecentPosts();
  
  return {
    props: { posts },
    revalidate: 60,  // Revalidate every minute
  };
}

// On-demand revalidation when post published
// (backend calls /api/revalidate after publish)

export default function Home({ posts }) {
  return (
    <div>
      {posts.map(post => (
        <Link href={`/posts/${post.slug}`} key={post.id}>
          <a>{post.title}</a>
        </Link>
      ))}
    </div>
  );
}
```

---

## Key Takeaways

**ISR (Server-Side):**
- ✅ Static page performance
- ✅ Automatic background updates
- ✅ Perfect SEO
- ✅ Scales infinitely (CDN cached)
- ✅ Users never wait for regeneration

**SWR (Client-Side):**
- ✅ Instant updates without page reload
- ✅ Optimistic UI updates
- ✅ Automatic revalidation (focus, reconnect)
- ✅ Built-in error handling & loading states
- ✅ Deduplicates requests

**Together:**
- ✅ Fast first load (ISR)
- ✅ Real-time updates (SWR)
- ✅ Best of static + dynamic
- ✅ Excellent UX

---

## Best Practices

### ISR

**1. Choose appropriate revalidate times:**
- Blog posts: 300-3600s (5min-1hour)
- Product pages: 60-300s (1-5min)
- News: 30-60s (high frequency)

**2. Use on-demand revalidation for immediate updates:**
```javascript
await res.revalidate(`/posts/${postId}`);
```

**3. Pre-render popular pages:**
```javascript
export async function getStaticPaths() {
  const popularIds = await fetchPopularPostIds();
  return {
    paths: popularIds.map(id => ({ params: { id } })),
    fallback: 'blocking'
  };
}
```

### SWR

**1. Use global config for consistency:**
```javascript
<SWRConfig value={{ dedupingInterval: 2000 }}>
```

**2. Set fallbackData for instant rendering:**
```javascript
useSWR('/api/posts', fetcher, { fallbackData: initialPosts });
```

**3. Disable auto-revalidation when not needed:**
```javascript
useSWR('/api/static-data', fetcher, {
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
});
```

**4. Use optimistic updates for instant UX:**
```javascript
mutate('/api/posts', updatedPosts, false);
```

---

## What's Next?

You now understand the complete caching stack:
1. **HTTP headers** - Browser & CDN control
2. **localStorage** - Client-side persistence
3. **CDN** - Edge caching worldwide
4. **ISR + SWR** - Framework-level caching

Next: Build real projects implementing each layer! 🚀

