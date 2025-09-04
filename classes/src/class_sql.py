# A place to keep sql statements

GET_CLASSES: str = """
SELECT class_id, class_name, hours_per_week, program_id, active
FROM classes
WHERE active = true
ORDER BY class_name;
"""

GET_CLASS_BY_CLASS_ID: str = """
SELECT class_id, class_name, hours_per_week, program_id, active
FROM classes
WHERE active = true
AND class_id = %(class_id)s;
"""

DELETE_CLASS: str = """
DELETE FROM classes WHERE class_id = %(class_id)s;
"""
