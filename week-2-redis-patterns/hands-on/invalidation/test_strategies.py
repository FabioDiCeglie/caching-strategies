"""
Test script demonstrating all 7 cache invalidation strategies
"""

import requests
import time

BASE_URL = "http://localhost:8004"


def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_result(label, value):
    print(f"   {label}: {value}")


def timed_request(method, url, **kwargs):
    """Make a timed HTTP request and return (response, duration_ms)"""
    start = time.time()
    response = getattr(requests, method)(url, **kwargs)
    duration = (time.time() - start) * 1000
    return response, duration


def test_health():
    """Health check"""
    print_header("🏥 Health Check")
    response = requests.get(f"{BASE_URL}/health")
    health = response.json()
    print_result("Status", health['status'])
    print_result("Database", health['database'])
    print_result("Redis", health['redis'])


def test_strategy_1_ttl():
    """Strategy 1: TTL (Time To Live)"""
    print_header("⏰ Strategy 1: TTL (Auto-Expiration)")
    
    product_id = 1
    
    # First request - Cache MISS
    print("\n🔍 Request 1 - Cache MISS")
    response, duration_miss = timed_request("get", f"{BASE_URL}/products/ttl/{product_id}")
    product = response.json()
    print_result("Product", product['name'])
    print_result("Cached", product.get('cached', False))
    print_result("Time", f"{duration_miss:.2f}ms")
    print_result("TTL", "60 seconds")
    
    # Second request - Cache HIT
    print("\n🔍 Request 2 - Cache HIT")
    response, duration_hit = timed_request("get", f"{BASE_URL}/products/ttl/{product_id}")
    product = response.json()
    print_result("Product", product['name'])
    print_result("Cached", product.get('cached', False))
    print_result("Time", f"{duration_hit:.2f}ms")
    
    # Show improvement
    improvement = duration_miss / duration_hit if duration_hit > 0 else 0
    print_result("🚀 Speedup", f"{improvement:.1f}x faster!")
    
    # Check TTL
    stats = requests.get(f"{BASE_URL}/cache/stats/product:ttl:{product_id}").json()
    print_result("Time remaining", f"{stats.get('ttl', 0)} seconds")
    
    print("\n💡 Key Learning: Cache expires automatically after 60s")


def test_strategy_2_explicit():
    """Strategy 2: Explicit Invalidation"""
    print_header("🗑️  Strategy 2: Explicit Invalidation (Delete on Write)")
    
    product_id = 2
    
    # Cache the product
    print("\n🔍 Step 1 - GET product (cache it)")
    response, duration = timed_request("get", f"{BASE_URL}/products/explicit/{product_id}")
    product = response.json()
    print_result("Product", product['name'])
    print_result("Cached", product.get('cached', False))
    print_result("Time", f"{duration:.2f}ms")
    
    # Verify it's cached
    print("\n🔍 Step 2 - GET again (should be cached)")
    response, duration = timed_request("get", f"{BASE_URL}/products/explicit/{product_id}")
    product = response.json()
    print_result("Cached", product.get('cached', False))
    print_result("Time", f"{duration:.2f}ms (FAST!)")
    
    # Delete the product
    print("\n🗑️  Step 3 - DELETE product (invalidates cache)")
    response, duration = timed_request("delete", f"{BASE_URL}/products/explicit/{product_id}")
    print_result("Result", response.json()['message'])
    print_result("Time", f"{duration:.2f}ms")
    
    # Try to get it (404)
    print("\n🔍 Step 4 - GET again (404 - not found)")
    response, duration = timed_request("get", f"{BASE_URL}/products/explicit/{product_id}")
    print_result("Status", response.status_code)
    print_result("Time", f"{duration:.2f}ms")
    
    print("\n💡 Key Learning: Cache deleted immediately when data changes")


def test_strategy_3_writethrough():
    """Strategy 3: Write-Through"""
    print_header("✏️  Strategy 3: Write-Through (Update Cache on Write)")
    
    product_id = 3
    
    # Cache the product
    print("\n🔍 Step 1 - GET product")
    response, duration = timed_request("get", f"{BASE_URL}/products/writethrough/{product_id}")
    product = response.json()
    print_result("Product", product['name'])
    print_result("Price", f"${product['price']}")
    print_result("Time", f"{duration:.2f}ms")
    
    # Update the product
    print("\n✏️  Step 2 - PUT update (updates cache too)")
    response, duration = timed_request("put", f"{BASE_URL}/products/writethrough/{product_id}", json={"price": 999.99})
    print_result("Updated", f"New price: ${response.json()['price']}")
    print_result("Time", f"{duration:.2f}ms")
    
    # Get again (cache hit with new data!)
    print("\n🔍 Step 3 - GET again (cache hit with NEW data)")
    response, duration = timed_request("get", f"{BASE_URL}/products/writethrough/{product_id}")
    product = response.json()
    print_result("Cached", product.get('cached', False))
    print_result("Price", f"${product['price']}")
    print_result("Time", f"{duration:.2f}ms (FAST!)")
    
    print("\n💡 Key Learning: Cache updated on write, next read is FAST")


def test_strategy_4_events():
    """Strategy 4: Event-Based Invalidation"""
    print_header("📢 Strategy 4: Event-Based (Pub/Sub)")
    
    product_id = 4
    
    # Cache the product
    print("\n🔍 Step 1 - GET product")
    response, duration = timed_request("get", f"{BASE_URL}/products/events/{product_id}")
    product = response.json()
    print_result("Product", product['name'])
    print_result("Time", f"{duration:.2f}ms")
    
    # Update and publish event
    print("\n✏️  Step 2 - PUT update (publishes event)")
    response, duration = timed_request("put", f"{BASE_URL}/products/events/{product_id}", json={"description": "Updated via event system"})
    print_result("Result", response.json()['message'])
    print_result("Time", f"{duration:.2f}ms")
    
    # Check cache (should be invalidated)
    print("\n🔍 Step 3 - GET again (cache miss after event)")
    response, duration = timed_request("get", f"{BASE_URL}/products/events/{product_id}")
    product = response.json()
    print_result("Cached", product.get('cached', False))
    print_result("Description", product['description'][:40] + "...")
    print_result("Time", f"{duration:.2f}ms")
    
    print("\n💡 Key Learning: Events notify other services to invalidate")


def test_strategy_5_swr():
    """Strategy 5: Stale-While-Revalidate"""
    print_header("⚡ Strategy 5: SWR (Always Fast)")
    
    # First request - Cache MISS
    print("\n🔍 Request 1 - Cache MISS")
    response, duration = timed_request("get", f"{BASE_URL}/products/featured")
    products = response.json()
    print_result("Products", f"{len(products)} featured items")
    print_result("Time", f"{duration:.2f}ms")
    
    # Second request - Cache HIT
    print("\n🔍 Request 2 - Cache HIT (fresh)")
    response, duration = timed_request("get", f"{BASE_URL}/products/featured")
    products = response.json()
    print_result("Cached", products[0].get('cached', False))
    print_result("Time", f"{duration:.2f}ms")
    
    # Wait for cache to get stale
    print("\n⏳ Waiting 95 seconds for cache to get stale...")
    print("   (TTL: 120s, stale threshold: 30s)")
    time.sleep(95)
    
    # Request with stale cache - still fast!
    print("\n🔍 Request 3 - Cache HIT (stale, but returned immediately)")
    response, duration = timed_request("get", f"{BASE_URL}/products/featured")
    products = response.json()
    print_result("Cached", products[0].get('cached', False))
    print_result("Time", f"{duration:.2f}ms (STILL FAST!)")
    print_result("Background", "Refreshing cache now...")
    
    print("\n💡 Key Learning: Always fast, refreshes in background")


def test_strategy_6_tags():
    """Strategy 6: Cache Tags"""
    print_header("🏷️  Strategy 6: Cache Tags (Group Invalidation)")
    
    category_id = 1  # Electronics
    
    # Cache all products in category
    print("\n🔍 Step 1 - GET all Electronics products")
    response, duration = timed_request("get", f"{BASE_URL}/products/by-category/{category_id}")
    products = response.json()
    print_result("Products", f"{len(products)} electronics")
    print_result("Tagged with", f"category:{category_id}")
    print_result("Time", f"{duration:.2f}ms")
    
    # Verify cached
    print("\n🔍 Step 2 - GET again (cached)")
    response, duration = timed_request("get", f"{BASE_URL}/products/by-category/{category_id}")
    products = response.json()
    print_result("Cached", products[0].get('cached', False))
    print_result("Time", f"{duration:.2f}ms (FAST!)")
    
    # Update category (invalidates ALL products with this tag)
    print("\n✏️  Step 3 - PUT update category (invalidates all tagged items)")
    response, duration = timed_request("put", f"{BASE_URL}/categories/{category_id}")
    print_result("Result", response.json()['message'])
    print_result("Time", f"{duration:.2f}ms")
    
    # Get again (cache miss for all products)
    print("\n🔍 Step 4 - GET again (all products cache miss)")
    response, duration = timed_request("get", f"{BASE_URL}/products/by-category/{category_id}")
    products = response.json()
    print_result("Cached", products[0].get('cached', False))
    print_result("Time", f"{duration:.2f}ms")
    
    print("\n💡 Key Learning: One operation invalidates many related items")


def test_strategy_7_production():
    """Strategy 7: Combined (Production Pattern)"""
    print_header("🔥 Strategy 7: PRODUCTION (TTL + Tags + Events)")
    
    product_id = 7
    
    # Cache the product
    print("\n🔍 Step 1 - GET product")
    response, duration = timed_request("get", f"{BASE_URL}/products/production/{product_id}")
    product = response.json()
    print_result("Product", product['name'])
    print_result("Category", product['category_name'])
    print_result("Features", "TTL (300s) + Tags + Events")
    print_result("Time", f"{duration:.2f}ms")
    
    # Verify cached
    print("\n🔍 Step 2 - GET again (cached)")
    response, duration = timed_request("get", f"{BASE_URL}/products/production/{product_id}")
    product = response.json()
    print_result("Cached", product.get('cached', False))
    print_result("Time", f"{duration:.2f}ms (FAST!)")
    
    # Update (uses all strategies)
    print("\n✏️  Step 3 - PUT update (uses all strategies)")
    response, duration = timed_request("put", f"{BASE_URL}/products/production/{product_id}", json={"name": "UPDATED: " + product['name']})
    print_result("Time", f"{duration:.2f}ms")
    print_result("Strategies used", "✅ Explicit delete")
    print_result("", "✅ Event published")
    print_result("", "✅ Tags invalidated")
    print_result("", "✅ TTL as safety net")
    
    print("\n💡 Key Learning: THIS is how real production systems work!")


def run_all_tests():
    """Run all strategy tests"""
    print("\n" + "🚀" * 35)
    print("   CACHE INVALIDATION STRATEGIES - COMPLETE DEMO")
    print("🚀" * 35)
    
    try:
        # Health check
        test_health()
        
        # Test each strategy
        test_strategy_1_ttl()
        test_strategy_2_explicit()
        test_strategy_3_writethrough()
        test_strategy_4_events()
        test_strategy_5_swr()
        test_strategy_6_tags()
        test_strategy_7_production()
        
        # Summary
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED!")
        print("="*70)
        print("\n📚 Summary:")
        print("   1. TTL: Auto-expiration (simple)")
        print("   2. Explicit: Delete on write (immediate consistency)")
        print("   3. Write-Through: Update on write (fast reads)")
        print("   4. Event-Based: Pub/Sub (microservices)")
        print("   5. SWR: Stale-while-revalidate (always fast)")
        print("   6. Cache Tags: Group invalidation (relationships)")
        print("   7. PRODUCTION: Combines best strategies ⭐")
        print("\n" + "="*70 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("   Make sure the server is running on http://localhost:8004")
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    run_all_tests()

