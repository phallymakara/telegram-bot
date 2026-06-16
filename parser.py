import re

def parse_report_line(line: str) -> dict:
    """
    Parses a single line of the report.
    Expected format: <index>. <name> <hours>h <note>?
    Example: "1. ប៉ែន ទិត្យ.   8 h MEP" -> index=1, name="ប៉ែន ទិត្យ", hours=8.0, note="MEP"
    Example: "2. អៀម អេន.    8.9 h" -> index=2, name="អៀម អេន", hours=8.9, note=None
    """
    # 1. Match the starting index: e.g., "1." or "1"
    index_match = re.match(r'^\s*(\d+)[\.\s]*', line)
    if not index_match:
        return None
    
    index_str = index_match.group(1)
    remaining = line[index_match.end():].strip()
    
    # 2. Search for the hours: a float/int followed by optional space and 'h' or 'H'
    hours_match = re.search(r'(\d+(?:\.\d+)?)\s*[hH](?:\s+|$)(.*)', remaining)
    if not hours_match:
        return None
    
    hours_str = hours_match.group(1)
    note_str = hours_match.group(2).strip() if hours_match.group(2) else None
    
    if note_str:
        note_str = re.sub(r'^\s*[,，;\.\s\-\/៖:]+', '', note_str)
        note_str = re.sub(r'[,，;\.\s\-\/៖:]+$', '', note_str).strip()
        if not note_str:
            note_str = None
            
    # The part before the hours is the employee's name
    name_part = remaining[:hours_match.start()].strip()
    
    # Clean the name of trailing dots/punctuation/spaces/colons
    name = re.sub(r'[:៖\.\s、，,]+$', '', name_part).strip()
    if not name:
        return None
        
    return {
        'index': int(index_str),
        'name': name,
        'hours': float(hours_str),
        'note': note_str
    }

def parse_report_text_by_days(text: str) -> list:
    """
    Parses a multiline text block containing attendance for one or more days.
    Returns a list of dicts, where each dict represents a day block:
    {
        'header': str or None,
        'workers': list of parsed worker dicts
    }
    """
    day_blocks = []
    current_day_workers = []
    current_header = None
    last_potential_header = None
    last_index = 0

    lines = text.split('\n')
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        
        parsed = parse_report_line(line) # Use original line for parsing to keep leading whitespace handling, or cleaned. Let's see: parse_report_line already handles line.
        if parsed:
            index = parsed['index']
            # If the index is 1, or if the index is less than or equal to the last seen index,
            # it indicates the start of a new day/list block.
            if index == 1 or index <= last_index:
                # Save the current day block if it has workers
                if current_day_workers:
                    day_blocks.append({
                        'header': current_header or f"Day {len(day_blocks) + 1}",
                        'workers': current_day_workers
                    })
                # Reset for the new day
                current_day_workers = []
                current_header = last_potential_header
                last_potential_header = None
            
            current_day_workers.append(parsed)
            last_index = index
        else:
            # Not a worker line. This could be a day header.
            # We save it as the last potential header.
            last_potential_header = cleaned

    # Add the last block
    if current_day_workers:
        day_blocks.append({
            'header': current_header or f"Day {len(day_blocks) + 1}",
            'workers': current_day_workers
        })

    return day_blocks

def parse_report_text(text: str) -> list:
    """
    Parses a multiline text block and returns list of parsed workers.
    """
    blocks = parse_report_text_by_days(text)
    workers = []
    for block in blocks:
        workers.extend(block['workers'])
    return workers
