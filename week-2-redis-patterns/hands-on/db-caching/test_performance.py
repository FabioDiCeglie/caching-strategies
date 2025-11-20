"""
Performance testing script for Blog API caching
Shows the dramatic difference between cache hits and misses
"""

import requests
import time

BASE_URL = "http://localhost:8003"


def test_get_all_posts():
    """Test GET /posts performance (500k records)"""
    print("\n" + "="*60)
    print("📊 Testing GET /posts (500,000 records)")
    print("="*60)
    
    # First request - Cache MISS
    print("\n🔍 Request 1: Cache MISS (querying database)...")
    start = time.time()
    response = requests.get(f"{BASE_URL}/posts")
    duration_miss = (time.time() - start) * 1000
    
    posts_count = len(response.json())
    print(f"   ⏱️  Time: {duration_miss:.2f}ms")
    print(f"   📦 Posts: {posts_count:,}")
    print(f"   💾 Cached: {response.json()[0].get('cached', False)}")
    
    # Second request - Cache HIT
    print("\n🔍 Request 2: Cache HIT (from Redis)...")
    start = time.time()
    response = requests.get(f"{BASE_URL}/posts")
    duration_hit = (time.time() - start) * 1000
    
    print(f"   ⏱️  Time: {duration_hit:.2f}ms")
    print(f"   📦 Posts: {len(response.json()):,}")
    print(f"   💾 Cached: {response.json()[0].get('cached', False)}")
    
    # Calculate improvement
    improvement = duration_miss / duration_hit
    print(f"\n🚀 Cache Performance: {improvement:.1f}x faster!")
    print(f"   Saved: {duration_miss - duration_hit:.2f}ms")


def test_get_single_post():
    """Test GET /posts/{id} performance"""
    print("\n" + "="*60)
    print("📊 Testing GET /posts/12345 (single record)")
    print("="*60)
    
    post_id = 12345
    
    # First request - Cache MISS
    print("\n🔍 Request 1: Cache MISS (querying database)...")
    start = time.time()
    response = requests.get(f"{BASE_URL}/posts/{post_id}")
    duration_miss = (time.time() - start) * 1000
    
    post = response.json()
    print(f"   ⏱️  Time: {duration_miss:.2f}ms")
    print(f"   📝 Title: {post['title']}")
    print(f"   💾 Cached: {post.get('cached', False)}")
    
    # Second request - Cache HIT
    print("\n🔍 Request 2: Cache HIT (from Redis)...")
    start = time.time()
    response = requests.get(f"{BASE_URL}/posts/{post_id}")
    duration_hit = (time.time() - start) * 1000
    
    post = response.json()
    print(f"   ⏱️  Time: {duration_hit:.2f}ms")
    print(f"   📝 Title: {post['title']}")
    print(f"   💾 Cached: {post.get('cached', False)}")
    
    # Calculate improvement
    improvement = duration_miss / duration_hit
    print(f"\n🚀 Cache Performance: {improvement:.1f}x faster!")
    print(f"   Saved: {duration_miss - duration_hit:.2f}ms")


def test_create_post():
    """Test POST /posts and cache invalidation"""
    print("\n" + "="*60)
    print("📊 Testing POST /posts (cache invalidation)")
    print("="*60)
    
    # Create new post
    print("\n📝 Creating new post...")
    new_post = {
        "title": "Testing Cache Invalidation",
        "content": "This post should invalidate the 'all posts' cache!",
        "author": "TestBot"
    }
    
    start = time.time()
    response = requests.post(f"{BASE_URL}/posts", json=new_post)
    duration = (time.time() - start) * 1000
    
    post = response.json()
    print(f"   ⏱️  Time: {duration:.2f}ms")
    print(f"   ✅ Created post ID: {post['id']}")
    print(f"   🗑️  Cache invalidated: post:all")
    
    # Next GET will be a cache MISS again
    print("\n🔍 Next GET /posts will be CACHE MISS (fresh data)...")


def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("🏥 Health Check")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    health = response.json()
    
    print(f"   Status: {health['status']}")
    print(f"   Database: {health['database']}")
    print(f"   Redis: {health['redis']}")


if __name__ == "__main__":
    print("\n🚀 Blog API Performance Testing")
    print("=" * 60)
    
    try:
        # Health check first
        test_health()
        
        # Test single post (fast)
        test_get_single_post()
        
        # Test all posts (slow due to size)
        test_get_all_posts()
        
        # Test cache invalidation
        test_create_post()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("   Make sure the server is running on http://localhost:8003")
    except Exception as e:
        print(f"\n❌ Error: {e}")

