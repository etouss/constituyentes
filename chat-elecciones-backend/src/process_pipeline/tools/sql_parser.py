import re

def parse_sql_query(sql_query):
    # Regular expression to match similar or SIMILAR clauses
    similar_pattern = re.compile(r'(?i)\bsimilar\((.*?)\)', re.IGNORECASE)
    
    # Find all similar clauses
    similar_clauses = re.findall(similar_pattern, sql_query)

    # Replace similar clauses with placeholders
    new_sql_query = re.sub(similar_pattern, 'TRUE', sql_query)

    return new_sql_query, similar_clauses