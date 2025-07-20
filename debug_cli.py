#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/itsatony/code/project2md')

from project2md.signature_processor import SignatureProcessor
from project2md.config import Config
from pathlib import Path

def debug_cli_processing():
    """Debug the CLI processing to see why signatures mode isn't working."""
    
    # Load config similar to CLI
    config = Config.from_yaml("")  # Default config
    config.signatures_mode = True
    
    print(f"Signatures mode: {config.signatures_mode}")
    
    # Test files from test_temp
    test_files = [
        ('config.yml', '/home/itsatony/code/project2md/test_temp/config.yml'),
        ('package.json', '/home/itsatony/code/project2md/test_temp/package.json'),
        ('empty_code.py', '/home/itsatony/code/project2md/test_temp/empty_code.py'),
    ]
    
    processor = SignatureProcessor()
    
    for name, path in test_files:
        file_path = Path(path)
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            print(f"\n--- Processing {name} ---")
            print(f"Original content length: {len(content)} chars")
            
            if config.signatures_mode:
                processed_content = processor.process_file(file_path, content)
                print(f"Processed content: {repr(processed_content)}")
            else:
                print("Signatures mode not enabled")
                
        except Exception as e:
            print(f"Error processing {name}: {e}")

if __name__ == "__main__":
    debug_cli_processing()
