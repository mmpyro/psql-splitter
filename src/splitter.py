#!/usr/bin/env python

import logging
import os
import re


def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)


def is_empty_or_comment(line: str, comment: str, multi_line_comment: str) -> bool:
    stripped = line.strip()
    if stripped == "":
        return True
    elif stripped.startswith(comment):
        return True
    elif stripped.startswith(multi_line_comment):
        return True
    elif stripped.endswith(multi_line_comment[::-1]):
        return True
    return False


def split_sql(file_path: str, chunk_size: int, separator: str, comment: str, multi_line_comment: str, compress: bool) -> None:
    total_size = get_file_size(file_path)
    if total_size == 0:
        raise ValueError(f"File {file_path} is empty.")
    elif chunk_size < 1:
        raise ValueError(f"Number of chunks has to be greater than 0 but was {chunk_size}")
    
    target_chunk_size = total_size / chunk_size
    logging.info(f"Target chunk size (bytes): {target_chunk_size}")

    with open(file_path, 'r') as s:
        current_chunk_index = 1
        current_chunk_bytes = 0
        total_bytes_processed = 0
        file = open(f"{current_chunk_index}.sql", 'w')
        
        in_copy_stdin = False
        dollar_quote_tag = None
        
        try:
            for line in s:
                if compress and is_empty_or_comment(line, comment, multi_line_comment):
                    # We should still count these towards processed bytes if we want accurate remaining bytes,
                    # but since they aren't written, they don't count towards chunk size.
                    total_bytes_processed += len(line.encode('utf-8'))
                    continue
                
                line_bytes = len(line.encode('utf-8'))
                file.write(line)
                current_chunk_bytes += line_bytes
                total_bytes_processed += line_bytes
                
                # Check for state changes BEFORE we check if we can split
                # But we only split on the line that ENDS the state or is OUTSIDE the state
                
                ends_block = False
                if in_copy_stdin:
                    if line.strip() == "\\.":
                        in_copy_stdin = False
                        ends_block = True
                elif dollar_quote_tag:
                    if dollar_quote_tag in line:
                        if line.count(dollar_quote_tag) % 2 != 0:
                            dollar_quote_tag = None
                            ends_block = True
                else:
                    if "COPY " in line and " FROM stdin;" in line:
                        in_copy_stdin = True
                    else:
                        match = re.search(r"(\$[a-zA-Z0-9_]*\$)", line)
                        if match:
                            tag = match.group(1)
                            if line.count(tag) % 2 != 0:
                                dollar_quote_tag = tag

                # Check if we should switch to a new chunk
                can_split = not in_copy_stdin and not dollar_quote_tag
                # We can split on a separator, OR on the line that just ended a block
                is_split_point = line.rstrip().endswith(separator) or ends_block
                
                if can_split and current_chunk_bytes >= target_chunk_size and is_split_point and current_chunk_index < chunk_size:
                    file.close()
                    current_chunk_index += 1
                    current_chunk_bytes = 0
                    
                    # Recalculate target size for remaining chunks
                    remaining_bytes = total_size - total_bytes_processed
                    remaining_chunks = chunk_size - current_chunk_index + 1
                    target_chunk_size = remaining_bytes / remaining_chunks
                    logging.info(f"New target chunk size: {target_chunk_size}")
                    
                    file = open(f"{current_chunk_index}.sql", 'w')
        finally:
            if file and not file.closed:
                file.close()
