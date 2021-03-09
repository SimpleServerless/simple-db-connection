# A place to keep sql statemennts

GET_STUDENTS: str = """
SELECT student_uuid, student_id, first_name, last_name, status, program_id
FROM students
WHERE active = true;
"""

GET_STUDENT_BY_STUDENT_ID: str = """
SELECT student_uuid, student_id, first_name, last_name, status, program_id
FROM students
WHERE active = true
AND student_id = %s;
"""

# Closest thing postgres has to an upsert
SAVE_STUDENT: str = """
INSERT INTO students (student_uuid, first_name, last_name, status, program_id, active, updated_by, created_by)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT(student_uuid) DO UPDATE
SET
  student_uuid = excluded.student_uuid,
  first_name = excluded.first_name,
  last_name = excluded.last_name,
  status = excluded.status,
  program_id = excluded.program_id,
  active = excluded.active,
  updated_by = excluded.updated_by
RETURNING student_id, student_uuid, first_name, last_name, status, program_id;
"""

INSERT_STUDENT: str = """
INSERT INTO students (student_uuid, first_name, last_name, status, program_id, active, updated_by, created_by)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
RETURNING student_id, student_uuid, first_name, last_name, status, program_id;
"""

UPDATE_STUDENT: str = """
UPDATE students
SET
    student_uuid = %s,
    first_name = %s,
    last_name = %s,
    status = %s,
    program_id = %s,
    active = %s,
    updated_by = %s
WHERE student_id = %s
RETURNING student_id, student_uuid, first_name, last_name, status, program_id;
"""