from collections import defaultdict

# Allowed violation classes for counting
ALLOWED_VIOLATIONS = {'No_helmet', 'No_Vest', 'No_goggles', 'No_SafetyShoes', 'No_Gloves'}

class ViolationCounter:
    def __init__(self):
        self.violation_counts = defaultdict(int)
        
    def count_violation(self, violation_type):
        """Count a specific violation type (only if it's an allowed violation)"""
        if violation_type in ALLOWED_VIOLATIONS:
            self.violation_counts[violation_type] += 1
            print(f"🚨 VIOLATION DETECTED: {violation_type} - Count: {self.violation_counts[violation_type]}")
        
    def get_counts(self):
        """Get current violation counts"""
        return dict(self.violation_counts)
    
    def reset_counts(self):
        """Reset all violation counts"""
        self.violation_counts.clear()
        print("🔄 Violation counts reset")

# Global violation counter instance
violation_counter = ViolationCounter()

def count_violation(violation_type):
    """Count a specific violation type"""
    violation_counter.count_violation(violation_type)

def get_violation_counts():
    """Get current violation counts"""
    return violation_counter.get_counts()

def reset_violation_counts():
    """Reset all violation counts"""
    violation_counter.reset_counts()
