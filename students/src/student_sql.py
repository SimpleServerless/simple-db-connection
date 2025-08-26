# A place to keep sql statemennts

GET_STUDENTS: str = """
SELECT student_uuid, student_id, first_name, last_name, status, program_id
FROM students
WHERE active = true
ORDER BY student_id;
"""

GET_STUDENT_BY_STUDENT_ID: str = """
SELECT student_uuid, student_id, first_name, last_name, status, program_id
FROM students
WHERE active = true
AND student_id = %s;
"""

# Closest thing postgres has to an upsert
SAVE_STUDENT: str = """
INSERT INTO students (student_uuid, student_id, first_name, last_name, status, program_id, active, updated_by, created_by)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT(student_id) DO UPDATE
SET
  student_uuid = excluded.student_uuid,
  student_id = excluded.student_id,
  first_name = excluded.first_name,
  last_name = excluded.last_name,
  status = excluded.status,
  program_id = excluded.program_id,
  active = excluded.active,
  updated_by = excluded.updated_by
RETURNING student_id, student_uuid, first_name, last_name, status, program_id;
"""
