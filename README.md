
# University Timetable Generator

Automatically generates optimized, conflict-free university timetables for multiple sections using Google OR-Tools, with formatted Excel export.

## Features
- Schedules theory and lab classes with teacher, room, and section constraints
- Avoids clashes for teachers/rooms/groups and balances workloads
- Enforces key rules (max classes/day, recess, parallel labs, etc.)
- Outputs master timetables for each weekday in a single Excel file

## Requirements
- Python 3.x
- ortools
- pandas
- openpyxl

Install all dependencies:
pip install ortools pandas openpyxl


## Usage
Edit input data (sections, subjects, labs, teachers, rooms) at the top of `timetable_generator.py`, then run:
python timetable_generator.py


Results are saved in `University_Master_Timetable.xlsx` (one sheet per day, formatted for clarity).

---

Made with  by Saroj Mohapatra
