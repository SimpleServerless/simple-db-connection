# A place to keep sql statemennts

GET_PROGRAMS: str = """
SELECT program_id, name, code, active
FROM programs
WHERE active = true
ORDER BY name;
"""

GET_PROGRAM_BY_PROGRAM_ID: str = """
SELECT program_id, name, code, active
FROM programs
WHERE active = true
AND program_id = %s;
"""

