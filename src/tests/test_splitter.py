import pytest
from unittest.mock import patch, mock_open, MagicMock, call
from src.splitter import get_file_size, is_empty_or_comment, split_sql

def test_get_file_size():
    with patch('os.path.getsize') as mock_getsize:
        mock_getsize.return_value = 100
        assert get_file_size("dummy.sql") == 100
        mock_getsize.assert_called_once_with("dummy.sql")

@pytest.mark.parametrize("line, comment, multi_line_comment, expected", [
    ("", "--", "/*", True),
    ("  ", "--", "/*", True),
    ("\n", "--", "/*", True),
    ("-- comment\n", "--", "/*", True),
    ("/* multi-line */\n", "--", "/*", True),
    ("SELECT * FROM users;\n", "--", "/*", False),
    ("INSERT INTO table VALUES (1);\n", "--", "/*", False),
    ("*/\n", "--", "/*", True),
])
def test_is_empty_or_comment(line, comment, multi_line_comment, expected):
    assert is_empty_or_comment(line, comment, multi_line_comment) == expected

def test_split_sql_empty_file():
    with patch('src.splitter.get_file_size') as mock_size:
        mock_size.return_value = 0
        with pytest.raises(ValueError, match="File dummy.sql is empty."):
            split_sql("dummy.sql", 2, ";", "--", "/*", False)

def test_split_sql_invalid_chunks():
    with patch('src.splitter.get_file_size') as mock_size:
        mock_size.return_value = 100
        with pytest.raises(ValueError, match="Number of chunks has to be greater than 0"):
            split_sql("dummy.sql", 0, ";", "--", "/*", False)

def test_split_sql_basic_splitting():
    # content: 4 lines, each 8 bytes (7 chars + \n)
    # Total size: 32 bytes
    content = "line11;\nline22;\nline33;\nline44;\n"
    content_bytes = content.encode('utf-8')
    total_size = len(content_bytes)
    
    # target_chunk_size = 32 / 2 = 16 bytes
    # line11;\n (8 bytes) + line22;\n (8 bytes) = 16 bytes.
    # line22;\n ends with ; so it should split here.
    
    mock_files = {}
    
    def m_open(path, mode='r'):
        m = MagicMock()
        m.__enter__.return_value = m
        if 'r' in mode:
            m.__iter__.return_value = content.splitlines(keepends=True)
        else:
            mock_files[path] = m
            # Mock write to capture content
            m.write = MagicMock()
        return m

    with patch('builtins.open', side_effect=m_open), \
         patch('src.splitter.get_file_size') as mock_size:
        
        mock_size.return_value = total_size
        
        split_sql("dummy.sql", 2, ";", "--", "/*", False)
        
        assert "1.sql" in mock_files
        assert "2.sql" in mock_files
        
        # Verify first chunk content
        first_chunk_calls = [c.args[0] for c in mock_files["1.sql"].write.call_args_list]
        assert first_chunk_calls == ["line11;\n", "line22;\n"]
        
        # Verify second chunk content
        second_chunk_calls = [c.args[0] for c in mock_files["2.sql"].write.call_args_list]
        assert second_chunk_calls == ["line33;\n", "line44;\n"]

def test_split_sql_with_compression():
    content = "-- comment\n\nSELECT 1;\n/* block */\nSELECT 2;\n"
    content_bytes = content.encode('utf-8')
    
    mock_files = {}
    def m_open(path, mode='r'):
        m = MagicMock()
        m.__enter__.return_value = m
        if 'r' in mode:
            m.__iter__.return_value = content.splitlines(keepends=True)
        else:
            mock_files[path] = m
            m.write = MagicMock()
        return m

    with patch('builtins.open', side_effect=m_open), \
         patch('src.splitter.get_file_size') as mock_size:
        
        mock_size.return_value = len(content_bytes)
        
        split_sql("dummy.sql", 1, ";", "--", "/*", True)
        
        assert "1.sql" in mock_files
        written = "".join([c.args[0] for c in mock_files["1.sql"].write.call_args_list])
        assert "SELECT 1;\nSELECT 2;\n" == written
        assert "-- comment" not in written
        assert "/* block */" not in written

def test_split_sql_separator_logic():
    # Only split if target size reached AND line ends with separator
    # content: 4 lines, each 8 bytes. Total 32.
    # target size = 32 / 2 = 16.
    # line11 (7 bytes) -> no separator
    # line22 (7 bytes) -> no separator
    # line33; (8 bytes) -> separator!
    content = "line11\nline22\nline33;\nline44;\n"
    content_bytes = content.encode('utf-8')
    total_size = len(content_bytes)

    mock_files = {}
    def m_open(path, mode='r'):
        m = MagicMock()
        m.__enter__.return_value = m
        if 'r' in mode:
            m.__iter__.return_value = content.splitlines(keepends=True)
        else:
            mock_files[path] = m
            m.write = MagicMock()
        return m

    with patch('builtins.open', side_effect=m_open), \
         patch('src.splitter.get_file_size') as mock_size:
        
        mock_size.return_value = total_size
        
        split_sql("dummy.sql", 2, ";", "--", "/*", False)
        
        # Should split after line33; because line11 and line22 don't have ;
        assert "1.sql" in mock_files
        first_chunk = "".join([c.args[0] for c in mock_files["1.sql"].write.call_args_list])
        assert first_chunk == "line11\nline22\nline33;\n"
        
        second_chunk = "".join([c.args[0] for c in mock_files["2.sql"].write.call_args_list])
        assert second_chunk == "line44;\n"

def test_split_sql_copy_command():
    # COPY should not be split after the semicolon on the same line
    # Make the first line long enough to exceed target_chunk_size
    content = "COPY long_table_name_to_force_split_early_if_not_handled FROM stdin;\nline1\nline2\n\\.\nSELECT 1;\n"
    content_bytes = content.encode('utf-8')
    total_size = len(content_bytes)
    
    # target_chunk_size = total_size / 2
    
    mock_files = {}
    def m_open(path, mode='r'):
        m = MagicMock()
        m.__enter__.return_value = m
        if 'r' in mode:
            m.__iter__.return_value = content.splitlines(keepends=True)
        else:
            mock_files[path] = m
            m.write = MagicMock()
        return m

    with patch('builtins.open', side_effect=m_open), \
         patch('src.splitter.get_file_size') as mock_size:
        
        mock_size.return_value = total_size
        
        # Split into 2 chunks
        split_sql("dummy.sql", 2, ";", "--", "/*", False)
        
        assert "1.sql" in mock_files
        first_chunk = "".join([c.args[0] for c in mock_files["1.sql"].write.call_args_list])
        # It should NOT split after 'COPY ... FROM stdin;'
        # The entire COPY block includes \.
        assert "COPY long_table_name_to_force_split_early_if_not_handled FROM stdin;" in first_chunk
        assert "line1" in first_chunk
        assert "line2" in first_chunk
        assert "\\." in first_chunk

def test_split_sql_dollar_quoting():
    content = "CREATE FUNCTION foo() AS $$\nBEGIN\n  PERFORM 1;\nEND;\n$$ LANGUAGE plpgsql;\nSELECT 2;\n"
    content_bytes = content.encode('utf-8')
    total_size = len(content_bytes)

    mock_files = {}
    def m_open(path, mode='r'):
        m = MagicMock()
        m.__enter__.return_value = m
        if 'r' in mode:
            m.__iter__.return_value = content.splitlines(keepends=True)
        else:
            mock_files[path] = m
            m.write = MagicMock()
        return m

    with patch('builtins.open', side_effect=m_open), \
         patch('src.splitter.get_file_size') as mock_size:
        
        mock_size.return_value = total_size
        
        split_sql("dummy.sql", 2, ";", "--", "/*", False)
        
        assert "1.sql" in mock_files
        first_chunk = "".join([c.args[0] for c in mock_files["1.sql"].write.call_args_list])
        # Should not split at 'PERFORM 1;' or 'END;'
        assert "PERFORM 1;" in first_chunk
        assert "END;" in first_chunk
        assert "$$ LANGUAGE plpgsql;" in first_chunk
