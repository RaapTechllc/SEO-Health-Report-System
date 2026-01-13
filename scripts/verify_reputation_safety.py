#!/usr/bin/env python3
"""
REPUTATION VERIFICATION SCRIPT
Final check to ensure no fake data or reputation risks remain.
"""

import os
import sys
import re

def scan_for_reputation_risks():
    """Scan all Python files for reputation-damaging patterns."""
    
    risks_found = []
    project_root = "/mnt/e/claude code projects/seo-health-report"
    
    # Patterns that could damage reputation
    dangerous_patterns = [
        (r'score.*50', "Fake score of 50"),
        (r'_placeholder.*True', "Placeholder data flag"),
        (r'TODO.*Implement', "TODO in production code"),
        (r'STUB.*API', "API stub in production"),
        (r'FIXME', "FIXME in production code"),
        (r'XXX', "XXX marker in production code"),
        (r'NotImplemented', "NotImplemented in production"),
        (r'mock.*data', "Mock data in production"),
        (r'fake.*score', "Fake score reference"),
        (r'placeholder.*result', "Placeholder result"),
    ]
    
    # Scan all Python files
    for root, dirs, files in os.walk(project_root):
        # Skip test directories and cache
        if any(skip in root for skip in ['test', '__pycache__', '.git', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for line_num, line in enumerate(content.split('\n'), 1):
                        for pattern, description in dangerous_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                risks_found.append({
                                    'file': filepath.replace(project_root, ''),
                                    'line': line_num,
                                    'content': line.strip(),
                                    'risk': description,
                                    'pattern': pattern
                                })
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return risks_found

def main():
    print("🔍 REPUTATION VERIFICATION SCAN")
    print("=" * 50)
    
    risks = scan_for_reputation_risks()
    
    if not risks:
        print("✅ NO REPUTATION RISKS FOUND")
        print("✅ System is safe for client delivery")
        print("✅ Both reputations are protected")
        return True
    
    print(f"🚨 FOUND {len(risks)} REPUTATION RISKS:")
    print("-" * 50)
    
    for risk in risks:
        print(f"🚨 {risk['file']}:{risk['line']}")
        print(f"   Risk: {risk['risk']}")
        print(f"   Code: {risk['content']}")
        print()
    
    print("❌ SYSTEM NOT SAFE FOR CLIENT DELIVERY")
    print("❌ REPUTATION RISKS MUST BE FIXED")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
