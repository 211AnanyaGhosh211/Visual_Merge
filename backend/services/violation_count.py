import json
import os
from datetime import datetime
from collections import defaultdict

class ViolationCounter:
    def __init__(self):
        self.violation_counts = defaultdict(int)
        self.total_violations = 0
        self.violation_log = []
        
    def count_violation(self, violation_type):
        """Count a specific violation type"""
        self.violation_counts[violation_type] += 1
        self.total_violations += 1
        
        # Log the violation with timestamp
        violation_record = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'violation_type': violation_type,
            'count': self.violation_counts[violation_type]
        }
        self.violation_log.append(violation_record)
        
        # Print to console
        print(f"🚨 VIOLATION DETECTED: {violation_type} - Total count: {self.violation_counts[violation_type]}")
        
    def get_counts(self):
        """Get current violation counts"""
        return dict(self.violation_counts)
    
    def get_total_violations(self):
        """Get total number of violations"""
        return self.total_violations
    
    def print_summary(self):
        """Print violation summary to console"""
        print("\n" + "="*50)
        print("📊 VIOLATION SUMMARY")
        print("="*50)
        
        if not self.violation_counts:
            print("✅ No violations detected")
        else:
            for violation_type, count in self.violation_counts.items():
                print(f"🔴 {violation_type}: {count}")
            print(f"\n📈 Total Violations: {self.total_violations}")
        
        print("="*50)
    
    def reset_counts(self):
        """Reset all violation counts"""
        self.violation_counts.clear()
        self.total_violations = 0
        self.violation_log.clear()
        print("🔄 Violation counts reset")
    
    def save_log(self, filepath="log/violation_log.json"):
        """Save violation log to file"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump({
                    'summary': dict(self.violation_counts),
                    'total_violations': self.total_violations,
                    'detailed_log': self.violation_log,
                    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, f, indent=2)
            print(f"📝 Violation log saved to {filepath}")
        except Exception as e:
            print(f"❌ Error saving violation log: {e}")

# Global violation counter instance
violation_counter = ViolationCounter()

def count_violation(violation_type):
    """Count a specific violation type"""
    violation_counter.count_violation(violation_type)

def get_violation_counts():
    """Get current violation counts"""
    return violation_counter.get_counts()

def get_total_violations():
    """Get total number of violations"""
    return violation_counter.get_total_violations()

def print_violation_summary():
    """Print violation summary to console"""
    violation_counter.print_summary()

def reset_violation_counts():
    """Reset all violation counts"""
    violation_counter.reset_counts()

def save_violation_log(filepath="log/violation_log.json"):
    """Save violation log to file"""
    violation_counter.save_log(filepath)

def process_detection_results(detection_results):
    """Process detection results and count violations"""
    violations_detected = []
    
    for detection in detection_results:
        class_name = detection.get('class_name', '')
        confidence = detection.get('confidence', 0)
        
        # Check for violation classes
        if class_name in ['NO_helmet', 'NO_Vest', 'NO_goggles'] and confidence > 0.5:
            violations_detected.append(class_name)
            count_violation(class_name)
    
    return violations_detected
