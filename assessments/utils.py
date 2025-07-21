def calculate_grade(total_mark):
    grading_scheme = [
        (80, 'A+', 4.0),
        (75, 'A', 3.75),
        (70, 'A-', 3.5),
        (65, 'B+', 3.25),
        (60, 'B', 3.0),
        (55, 'B-', 2.75),
        (50, 'C+', 2.5),
        (45, 'C', 2.25),
        (40, 'D', 2.0),
        (0, 'F', 0.0)
    ]

    for threshold, grade, point in grading_scheme:
        if total_mark >= threshold:
            return {
                'grade': grade,
                'grade_point': point
            }
