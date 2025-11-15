#!/usr/bin/env python3
"""
Script to clean JSON corruption from all files in the repository.
"""

import os
import re
import glob

def clean_file(filepath):
    """Remove JSON corruption from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove JSON corruption pattern
        pattern = r'```json\{"\$mid":\d+,"mimeType":"[^"]+","data":\{"type":"Buffer","data":\[[^\]]+\]\}\}'
        cleaned_content = re.sub(pattern, '', content)
        
        # Also remove standalone JSON corruption
        pattern2 = r'\{"\$mid":\d+,"mimeType":"[^"]+","data":\{"type":"Buffer","data":\[[^\]]+\]\}\}'
        cleaned_content = re.sub(pattern2, '', cleaned_content)
        
        if cleaned_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            print(f"Cleaned: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error cleaning {filepath}: {e}")
        return False

def main():
    """Clean all files in the repository."""
    file_patterns = [
        '**/*.py',
        '**/*.md', 
        '**/*.yaml',
        '**/*.yml',
        '**/*.html',
        '**/*.css',
        '**/*.js',
        '**/*.json'
    ]
    
    cleaned_count = 0
    for pattern in file_patterns:
        for filepath in glob.glob(pattern, recursive=True):
            if clean_file(filepath):
                cleaned_count += 1
    
    print(f"Cleaned {cleaned_count} files")

if __name__ == "__main__":
    main()