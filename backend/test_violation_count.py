#!/usr/bin/env python3
"""
Test script to demonstrate violation counting functionality
"""

from services.violation_count import (
    count_violation, 
    get_violation_counts, 
    get_total_violations, 
    print_violation_summary, 
    reset_violation_counts, 
    save_violation_log
)

def test_violation_counting():
    """Test the violation counting system"""
    print("🧪 Testing Violation Counting System")
    print("=" * 50)
    
    # Reset counts
    reset_violation_counts()
    
    # Simulate some violations
    test_violations = [
        'NO_helmet',
        'NO_Vest', 
        'NO_goggles',
        'NO_helmet',
        'NO_Vest',
        'NO_helmet',
        'NO_goggles',
        'NO_Vest',
        'NO_goggles',
        'NO_helmet'
    ]
    
    print("📊 Simulating violations...")
    for violation in test_violations:
        count_violation(violation)
    
    # Print summary
    print_violation_summary()
    
    # Get counts programmatically
    counts = get_violation_counts()
    total = get_total_violations()
    
    print(f"\n📈 Programmatic access:")
    print(f"   Individual counts: {counts}")
    print(f"   Total violations: {total}")
    
    # Save log
    save_violation_log("log/test_violation_log.json")
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    test_violation_counting()
