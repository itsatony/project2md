#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/itsatony/code/project2md')

from project2md.signature_processor import SignatureProcessor
from pathlib import Path

def test_processor():
    processor = SignatureProcessor()
    
    # Test YAML
    yaml_content = """database:
  host: localhost
  port: 5432
  name: testdb"""
    
    result = processor.process_file(Path('config.yml'), yaml_content)
    print(f"YAML result: {repr(result)}")
    
    # Test JSON
    json_content = """{
  "name": "test",
  "version": "1.0"
}"""
    
    result = processor.process_file(Path('package.json'), json_content)
    print(f"JSON result: {repr(result)}")
    
    # Test empty Python
    empty_python = """import os
# just a comment"""
    
    result = processor.process_file(Path('empty.py'), empty_python)
    print(f"Empty Python result: {repr(result)}")

if __name__ == "__main__":
    test_processor()
