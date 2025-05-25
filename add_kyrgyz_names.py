from lxml import etree
import os
import time
import signal
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

last_save_time = time.monotonic()
SAVE_INTERVAL = 300
interrupted = False

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    exit(1)
client = genai.Client(api_key=api_key)

TRANSLATION_PROMPT = """Translate the following Russian street name to Kyrgyz, following these examples:

*   Керимбекова Кульчоро улица - Керимбеков Күлчоро көчөсү
*   Джеты-Огузский переулок - Жети-Өгүз чолок көчөсү
*   Джамбула переулок - Жамбыл чолок көчөсү
*   Кулиева улица - Кулиев көчөсү
*   Ладожская улица - Ладожская көчөсү
*   Асановой Динары улица - Асанова Динара көчөсү
*   Айтматова Торекула улица - Айтматов Төрөкул көчөсү
*   Мусы Джалиля улица - Муса Жалил көчөсү
*   Иссык-Кульская улица - Ысык-Көл көчөсү
*   Ибраимова улица - Ибраимов көчөсү
*   Исанова улица - Исанов көчөсү
*   Елебесова улица - Елебесов көчөсү
*   Верхняя улица - Верхняя көчөсү
*   Васильевский тракт - Васильев жолу
*   Ак-Булакский переулок - Ак-Булак чолок көчөсү
*   Объездная автомагистраль - Айланма автомагистраль
*   Минжилкиева улица - Минжылкиев көчөсү
*   Коенкозова Аширбая - Коёнкөзов Аширбай көчөсү
*   Калыка Акиева улица - Калык Акиев көчөсү
*   Джергаланский переулок - Жыргалаң чолок көчөсү
*   Куренкеева Мураталы улица - Күрөңкеев Муратаалы көчөсү
Translate: "{}"

Output only the Kyrgyz translation. Do not include any introductory or explanatory text. If the name includes "улица" or "переулок", translate it to "көчөсү" or "чолок көчөсү" respectively, and ensure the name order is preserved (e.g. Surname Name көчөсү)
"""

def signal_handler(sig, frame):
    """Handle interruption signals (e.g., Ctrl+C) to save progress."""
    global interrupted
    print('\n\nInterruption detected! Saving progress...')
    interrupted = True

def set_or_update_tag(element, tag_key, tag_value):
    """Set a new tag or update an existing tag in an XML element."""
    for tag in element.findall('tag'):
        if tag.get('k') == tag_key:
            tag.set('v', tag_value)
            return
    new_tag = etree.SubElement(element, 'tag')
    new_tag.set('k', tag_key)
    new_tag.set('v', tag_value)

def get_kyrgyz_translation(text_to_translate):
    """Get Kyrgyz translation for a Russian street name using Gemini API."""
    
    try:
        prompt = TRANSLATION_PROMPT.format(text_to_translate)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(response_mime_type="text/plain"),
        )
        translation = response.text.strip()
        return translation if translation else None
    except Exception as e:
        print(f"Error during API call for '{text_to_translate}': {e}")
        return None

def save_progress(tree, output_file, processed_count, total_count):
    """Save the current XML tree to a file."""
    global last_save_time
    try:
        tree.write(output_file, encoding='utf-8', xml_declaration=True, pretty_print=True)
        last_save_time = time.monotonic()
        print(f"Progress saved: {processed_count}/{total_count} streets processed. File: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving progress: {e}")
        return False

def load_review_progress():
    """Load review progress from progress.txt file."""
    progress_file = 'progress.txt'
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                content = f.read().strip()
                if content:
                    return int(content)
        except (ValueError, IOError):
            pass
    return 0

def save_review_progress(index):
    """Save current review progress to progress.txt file."""
    progress_file = 'progress.txt'
    try:
        with open(progress_file, 'w') as f:
            f.write(str(index))
        return True
    except IOError:
        return False

def is_already_processed(way):
    """Check if a way has both 'name:ru' and 'name:ky' tags."""
    has_ru = any(tag.get('k') == 'name:ru' for tag in way.findall('tag'))
    has_ky = any(tag.get('k') == 'name:ky' for tag in way.findall('tag'))
    return has_ru and has_ky

def process_streets(tree, output_file, temp_file, review_mode=False, review_limit=10):
    """Process streets in the OSM file, translating names to Kyrgyz."""
    global interrupted
    streets_to_translate = [(way, way.find("tag[@k='name']").get('v'))
                           for way in tree.findall('.//way')
                           if way.find("tag[@k='name']") is not None]
    total_streets = len(streets_to_translate)
    print(f"Found {total_streets} streets to process")
    
    processed_count = 0
    errors = 0
    skipped = 0
    
    if review_mode:
        start_index = load_review_progress()
        review_count = 0
        
        print(f"\n=== REVIEW MODE: Processing up to {review_limit} items with individual approval ===")
        if start_index > 0:
            print(f"Resuming from item {start_index + 1} (skipping {start_index} already reviewed items)")
        print("Commands: (y)es, (n)o, (e)dit, (q)uit, (c)ontinue without limit")
        
        for i, (way, original_name) in enumerate(streets_to_translate):
            if i < start_index:
                way_id = way.get('id')
                if is_already_processed(way):
                    skipped += 1
                continue
            
            if interrupted or review_count >= review_limit:
                save_review_progress(i)
                break
                
            way_id = way.get('id')
            if is_already_processed(way):
                skipped += 1
                save_review_progress(i + 1)
                continue
                
            review_count += 1
            print(f"\n[{review_count}/{review_limit}] Way ID: {way_id} (Item {i + 1}/{total_streets})")
            print(f"Original (Russian): {original_name}")
            
            kyrgyz_name = get_kyrgyz_translation(original_name)
            
            if kyrgyz_name and kyrgyz_name != original_name:
                print(f"Proposed (Kyrgyz): {kyrgyz_name}")
                
                while True:
                    response = input("Apply this translation? (y/n/e/q/c): ").strip().lower()
                    
                    if response == 'y':
                        set_or_update_tag(way, 'name:ky', kyrgyz_name)
                        set_or_update_tag(way, 'name:ru', original_name)
                        set_or_update_tag(way, 'name', kyrgyz_name)
                        processed_count += 1
                        print(f"✓ Applied translation")
                        break
                    elif response == 'n':
                        print(f"✗ Skipped translation")
                        break
                    elif response == 'e':
                        edited_name = input(f"Enter corrected Kyrgyz name: ").strip()
                        if edited_name:
                            set_or_update_tag(way, 'name:ky', edited_name)
                            set_or_update_tag(way, 'name:ru', original_name)
                            set_or_update_tag(way, 'name', edited_name)
                            processed_count += 1
                            print(f"✓ Applied edited translation: {edited_name}")
                        else:
                            print("✗ No edit provided, skipping")
                        break
                    elif response == 'q':
                        print("Quitting review mode...")
                        save_review_progress(i)
                        interrupted = True
                        break
                    elif response == 'c':
                        print("Continuing without review limit...")
                        review_limit = float('inf')
                        break
                    else:
                        print("Invalid input. Use y/n/e/q/c")
            else:
                print(f"✗ Failed to translate '{original_name}'")
                errors += 1
            
            save_review_progress(i + 1)
            
            if interrupted:
                break
        
        if not interrupted and i >= len(streets_to_translate) - 1:
            if os.path.exists('progress.txt'):
                os.remove('progress.txt')
                print("Review completed! Progress file removed.")
        
        return review_count + skipped, processed_count, errors, skipped
    
    for i, (way, original_name) in enumerate(streets_to_translate):
        if interrupted:
            print("Processing interrupted by user.")
            break
        
        way_id = way.get('id')
        if is_already_processed(way):
            skipped += 1
            if skipped <= 5:
                print(f"Skipping Way ID: {way_id} (already processed)")
            elif skipped == 6:
                print("... (skipping further already-processed ways)")
            continue
        
        print(f"\n[{i + 1 - skipped}] Way ID: {way_id}, Original Name: {original_name}")
        kyrgyz_name = get_kyrgyz_translation(original_name)
        
        if kyrgyz_name and kyrgyz_name != original_name:
            print(f"  ✓ Translated to Kyrgyz: {kyrgyz_name}")
            # 1) Add name:ky with Kyrgyz translation
            set_or_update_tag(way, 'name:ky', kyrgyz_name)
            # 2) Add name:ru with Russian name (move from `name`)
            set_or_update_tag(way, 'name:ru', original_name)
            # 3) Copy `name:ky` to `name` field
            set_or_update_tag(way, 'name', kyrgyz_name)
            processed_count += 1
        else:
            print(f"  ✗ Failed to translate '{original_name}'. Adding name:ru only.")
            set_or_update_tag(way, 'name:ru', original_name)
            errors += 1
        
        if time.monotonic() - last_save_time > SAVE_INTERVAL:
            save_progress(tree, temp_file, processed_count + errors, total_streets)
    
    if interrupted:
        save_progress(tree, temp_file, processed_count + errors, total_streets)
    
    return total_streets, processed_count, errors, skipped

def main():
    """Main function to process the OSM file and translate street names."""
    import sys
    
    review_mode = False
    review_limit = 10
    input_osm_file = None

    # Parse arguments
    args = sys.argv[1:]  # Exclude script name
    i = 0
    
    while i < len(args):
        arg = args[i]
        
        if arg == '--review':
            review_mode = True
            # Check if next argument is a number (review limit)
            if i + 1 < len(args) and args[i + 1].isdigit():
                review_limit = int(args[i + 1])
                i += 2  # Skip both --review and the number
            else:
                i += 1  # Skip just --review, keep default limit
        elif not arg.startswith('-'):
            # This should be the input file
            if input_osm_file is None:
                input_osm_file = arg
            i += 1
        else:
            # Unknown flag
            print(f"Unknown flag: {arg}")
            sys.exit(1)
    
    if not input_osm_file:
        print("Usage: python add_kyrgyz_names.py <input_osm_file> [--review [limit]]")
        print("Examples:")
        print("  python add_kyrgyz_names.py streets.osm")
        print("  python add_kyrgyz_names.py streets.osm --review")
        print("  python add_kyrgyz_names.py streets.osm --review 25")
        print("  python add_kyrgyz_names.py --review 50 streets.osm")
        sys.exit(1)
        
    # input_osm_file = 'streets_with_no_kyrgyz_names.osm' # Old hardcoded value
    output_osm_file = 'streets_with_kyrgyz_translations.osm'
    temp_output_file = 'streets_with_kyrgyz_translations_temp.osm'
    
    print(f"Processing OSM file: {input_osm_file}")
    if review_mode:
        print(f"REVIEW MODE: Will process up to {review_limit} items for manual review")
    
    try:
        # Load from temp file if it exists to resume progress
        if os.path.exists(temp_output_file):
            print(f"Resuming from {temp_output_file}")
            tree = etree.parse(temp_output_file)
        else:
            print(f"Starting with {input_osm_file}")
            tree = etree.parse(input_osm_file)
        
        print("\n--- Translating Street Names ---")
        total, processed, errors, skipped = process_streets(tree, output_osm_file, temp_output_file, review_mode, review_limit)
        
        print(f"\n--- Final Summary ---")
        print(f"Total streets found: {total}")
        print(f"Already processed (skipped): {skipped}")
        print(f"Successfully translated: {processed}")
        print(f"Translation failures: {errors}")
        
        if processed > 0 or errors > 0:
            tree.write(temp_output_file, encoding='utf-8', xml_declaration=True, pretty_print=True)
            os.replace(temp_output_file, output_osm_file)
            print(f"\nFinal OSM data written to '{output_osm_file}'")
        else:
            print("\nNo new streets processed.")
            if os.path.exists(temp_output_file):
                os.remove(temp_output_file)
    
    except IOError as e:
        print(f"Error: Cannot read file: {e}")
    except etree.XMLSyntaxError:
        print(f"Error: Invalid XML in input file.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()