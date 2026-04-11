import json
import os
import glob
from pathlib import Path

def extract_json_content(directory_path="."):
    """
    Extract and print content from all JSON files in the specified directory
    """
    # Find all JSON files in the directory and subdirectories
    json_files = glob.glob(os.path.join(directory_path, "**/*.json"), recursive=True)
    
    if not json_files:
        print("No JSON files found in the specified directory.")
        return
    
    print(f"Found {len(json_files)} JSON file(s)\n")
    print("="*80)
    
    for json_file in json_files:
        try:
            # Read and parse JSON file
            with open(json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            print(f"\n📄 File: {json_file}")
            print("-" * 50)
            
            # Pretty print the JSON content
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("-" * 50)
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {json_file}: {e}")
        except Exception as e:
            print(f"❌ Error reading {json_file}: {e}")

def extract_and_save_to_file(output_file="extracted_json_content.txt"):
    """
    Extract content from all JSON files and save to a text file
    """
    json_files = glob.glob("**/*.json", recursive=True)
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("EXTRACTED JSON CONTENT\n")
        outfile.write("="*80 + "\n\n")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as infile:
                    data = json.load(infile)
                    
                outfile.write(f"File: {json_file}\n")
                outfile.write("-"*50 + "\n")
                outfile.write(json.dumps(data, indent=2, ensure_ascii=False))
                outfile.write("\n\n" + "="*80 + "\n\n")
                
            except Exception as e:
                outfile.write(f"Error reading {json_file}: {e}\n\n")
    
    print(f"✅ Content saved to {output_file}")

# Simple function to just print line by line if JSON is simple
def print_json_line_by_line(directory_path="."):
    """
    Print JSON content line by line for simple JSON structures
    """
    json_files = glob.glob(os.path.join(directory_path, "**/*.json"), recursive=True)
    
    for json_file in json_files:
        print(f"\n{'='*60}")
        print(f"FILE: {json_file}")
        print('='*60)
        
        try:
            with open(json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # If JSON is a list or dict with simple structure
            if isinstance(data, list):
                for i, item in enumerate(data, 1):
                    print(f"{i}. {item}")
            elif isinstance(data, dict):
                for key, value in data.items():
                    print(f"{key}: {value}")
            else:
                print(data)
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Option 1: Just print to console
    extract_json_content(".")
    
    # Option 2: Save to file (uncomment to use)
    # extract_and_save_to_file("extracted_json_content.txt")
    
    # Option 3: Print line by line for simple JSON (uncomment to use)
    # print_json_line_by_line(".")