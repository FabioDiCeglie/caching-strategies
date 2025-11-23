"""
Concurrent booking test - demonstrates race condition vs distributed locks
"""

import requests
import concurrent.futures
import time


BASE_URL = "http://localhost:8005"


def book_ticket(event_id, user_name, use_lock=False):
    """Attempt to book a ticket"""
    endpoint = f"/book-with-lock/{event_id}" if use_lock else f"/book-no-lock/{event_id}"
    
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            json={"user_name": user_name},
            timeout=10
        )
        return {
            "user": user_name,
            "success": response.json().get("success"),
            "message": response.json().get("message"),
            "booking_id": response.json().get("booking_id")
        }
    except Exception as e:
        return {
            "user": user_name,
            "success": False,
            "message": f"Error: {str(e)}",
            "booking_id": None
        }


def reset_event(event_id):
    """Reset event for testing"""
    response = requests.post(f"{BASE_URL}/reset/{event_id}")
    return response.json()


def get_event(event_id):
    """Get event status"""
    response = requests.get(f"{BASE_URL}/events/{event_id}")
    return response.json()


def test_without_lock():
    """Test concurrent booking WITHOUT lock - shows race condition"""
    print("\n" + "="*70)
    print("🚨 TEST 1: WITHOUT LOCK (Race Condition)")
    print("="*70)
    
    event_id = 1  # Event with only 1 ticket
    num_users = 5
    
    # Reset event
    print("\n📋 Setup: Resetting event to 1 ticket...")
    reset_event(event_id)
    
    initial_state = get_event(event_id)
    print(f"   Event: {initial_state['name']}")
    print(f"   Available tickets: {initial_state['available_tickets']}")
    print(f"   Total attempts: {num_users} users")
    
    # Simulate 5 users trying to book simultaneously
    print(f"\n🏃 Simulating {num_users} concurrent booking requests...")
    
    users = [f"User{i+1}" for i in range(num_users)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(book_ticket, event_id, user, False) for user in users]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Show results
    print("\n📊 Results:")
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"   {status} {result['user']}: {result['message']}")
    
    # Final state
    final_state = get_event(event_id)
    print(f"\n📈 Final State:")
    print(f"   Successful bookings: {len(successful)}")
    print(f"   Failed bookings: {len(failed)}")
    print(f"   Available tickets: {final_state['available_tickets']}")
    print(f"   Total booked: {final_state['booked']}")
    
    # Check for overselling
    if len(successful) > initial_state['available_tickets']:
        print(f"\n💥 RACE CONDITION DETECTED!")
        print(f"   Expected: {initial_state['available_tickets']} booking(s)")
        print(f"   Actual: {len(successful)} booking(s)")
        print(f"   Oversold by: {len(successful) - initial_state['available_tickets']} ticket(s)")
    
    return len(successful), initial_state['available_tickets']


def test_with_lock():
    """Test concurrent booking WITH lock - prevents race condition"""
    print("\n" + "="*70)
    print("✅ TEST 2: WITH LOCK (Distributed Lock)")
    print("="*70)
    
    event_id = 1  # Same event with 1 ticket
    num_users = 5
    
    # Reset event
    print("\n📋 Setup: Resetting event to 1 ticket...")
    reset_event(event_id)
    
    initial_state = get_event(event_id)
    print(f"   Event: {initial_state['name']}")
    print(f"   Available tickets: {initial_state['available_tickets']}")
    print(f"   Total attempts: {num_users} users")
    
    # Simulate 5 users trying to book simultaneously
    print(f"\n🏃 Simulating {num_users} concurrent booking requests...")
    
    users = [f"User{i+1}" for i in range(num_users)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(book_ticket, event_id, user, True) for user in users]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Show results
    print("\n📊 Results:")
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"   {status} {result['user']}: {result['message']}")
    
    # Final state
    final_state = get_event(event_id)
    print(f"\n📈 Final State:")
    print(f"   Successful bookings: {len(successful)}")
    print(f"   Failed bookings: {len(failed)}")
    print(f"   Available tickets: {final_state['available_tickets']}")
    print(f"   Total booked: {final_state['booked']}")
    
    # Verify correctness
    if len(successful) == initial_state['available_tickets']:
        print(f"\n✅ LOCK WORKED!")
        print(f"   Exactly {len(successful)} booking(s) - NO overselling!")
    
    return len(successful), initial_state['available_tickets']


def run_tests():
    """Run both tests and compare"""
    print("\n" + "🔒" * 35)
    print("   DISTRIBUTED LOCKS DEMONSTRATION")
    print("🔒" * 35)
    
    try:
        # Test without lock
        no_lock_booked, expected = test_without_lock()
        
        # Wait a bit
        time.sleep(1)
        
        # Test with lock
        with_lock_booked, _ = test_with_lock()
        
        # Summary
        print("\n" + "="*70)
        print("📋 SUMMARY")
        print("="*70)
        print(f"\n   WITHOUT LOCK:")
        print(f"      Expected bookings: {expected}")
        print(f"      Actual bookings: {no_lock_booked}")
        print(f"      Result: {'❌ OVERSOLD!' if no_lock_booked > expected else '✅ OK'}")
        
        print(f"\n   WITH LOCK:")
        print(f"      Expected bookings: {expected}")
        print(f"      Actual bookings: {with_lock_booked}")
        print(f"      Result: {'✅ CORRECT!' if with_lock_booked == expected else '❌ ERROR'}")
        
        print("\n" + "="*70)
        print("💡 KEY TAKEAWAY:")
        print("   Without locks: Race conditions cause data corruption")
        print("   With locks: Serialized access ensures data integrity")
        print("="*70 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("   Make sure the server is running on http://localhost:8005")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    run_tests()

