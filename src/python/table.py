import random
import json
import pandas as pd
from ortools.sat.python import cp_model



# ----------------------------
# CONFIGURATIONS / INPUT DATA
# ----------------------------
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
ALL_SLOTS = ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4", "4-5"]
# Labs are 2-hour blocks; allowed starts correspond to 9-11, 11-1, 3-5
LAB_SLOT_STARTS = ["9-10", "11-12", "3-4"]
GROUPS = ['A', 'B']

SECTIONS = [
    'CSE-3-1', 'CSE-3-2', 'AIML-3',
    'CSE-5', 'IT-5',
    'CSE-7', 'IT-7'
]

SECTION_THEORY_ROOM = {
    'CSE-3-1': 'B-209', 'CSE-3-2': 'B-209', 'AIML-3': 'A-32',
    'CSE-5': 'B-205', 'IT-5': 'B-205', 'CSE-7': 'D-303', 'IT-7': 'D-303'
}

LAB_ROOMS = ['CS105', 'CS106', 'CS107', 'CS115', 'CS204', 'CS205', 'CS208', 'CS220']

SUBJECTS = {
    'CSE-3-1': [('DLD', 'AM'), ('DS', 'SK'), ('DBE', 'SP'), ('OOP', 'AVL')],
    'CSE-3-2': [('DLD', 'SWP'), ('DS', 'GS'), ('DBE', 'KN'), ('OOP', 'SS')],
    'AIML-3':  [('DLD', 'PKS'), ('DS', 'SKS'), ('DBE', 'GF4'), ('OOP', 'SKB')],
    'CSE-5':   [('TOC', 'GF2'), ('OS', 'HSB'), ('AI/ML', 'PKD'), ('CNS', 'SPanda')],
    'IT-5':    [('TOC', 'KKS'), ('OS', 'SBD'), ('AI/ML', 'GF3'), ('DMDW', 'BN')],
    'CSE-7':   [('AI', 'GF5'), ('IWP', 'GF6'), ('IP', 'KN'),('SM', 'SPS')],
    'IT-7':    [('AI', 'MRS'), ('CS', 'AD'), ('SM', 'SKN')]
}

LABS = {
    'CSE-3-1': ['DLD Lab', 'DS Lab', 'DBE Lab', 'OOP Lab'],
    'CSE-3-2': ['DLD Lab', 'DS Lab', 'DBE Lab', 'OOP Lab'],
    'AIML-3':  ['DLD Lab', 'DS Lab', 'DBE Lab', 'OOP Lab'],
    'CSE-5':   ['TOC Lab', 'OS Lab', 'AI/ML Lab'],
    'IT-5':    ['TOC Lab', 'OS Lab', 'AI/ML Lab'],
    'CSE-7':   ['Web Programming Lab','Seminar Lab'],
    'IT-7':    ['Artificial Intelligence Lab','Seminar Lab']
}

# helper to derive teacher for a lab from subject mapping
def get_teacher_for_lab(section, lab_name):
    subject_name_map = {'Web Programming Lab': 'IWP', 'Artificial Intelligence Lab': 'AI', 'Seminar Lab': 'SM'}
    subject_name = subject_name_map.get(lab_name, lab_name.replace(' Lab', ''))
    for subject, teacher in SUBJECTS.get(section, []):
        if subject == subject_name:
            return teacher
    return None

ALL_TEACHERS = sorted(list(set(teacher for section_subjects in SUBJECTS.values() for _, teacher in section_subjects)))
ALL_ROOMS = sorted(list(set(SECTION_THEORY_ROOM.values()) | set(LAB_ROOMS)))

# gather unique lab names across all sections
LAB_NAMES = sorted(list({lab for labs in LABS.values() for lab in labs}))

# ----------------------------
# BUILD CP-SAT MODEL
# ----------------------------
model = cp_model.CpModel()

# class_vars key: (section, group, subject, teacher, day_idx, slot_idx, room)
class_vars = {}

# Theory class variables (group 'ALL' means full section)
for section in SECTIONS:
    theory_room = SECTION_THEORY_ROOM.get(section)
    if not theory_room:
        continue
    for subject, teacher in SUBJECTS.get(section, []):
        for day_idx in range(len(DAYS)):
            for slot_idx in range(len(ALL_SLOTS)):
                name = f"theory_{section}_{subject}_{day_idx}_{slot_idx}"
                class_vars[(section, 'ALL', subject, teacher, day_idx, slot_idx, theory_room)] = model.NewBoolVar(name)

# Lab variables: group A/B, only start at LAB_SLOT_STARTS; room choice included
for section in LABS:
    for lab_name in LABS.get(section, []):
        teacher = get_teacher_for_lab(section, lab_name)
        if not teacher:
            continue
        for group in GROUPS:
            for day_idx in range(len(DAYS)):
                for slot_idx, slot in enumerate(ALL_SLOTS):
                    if slot not in LAB_SLOT_STARTS:
                        continue
                    for room in LAB_ROOMS:
                        name = f"lab_{section}_{group}_{lab_name}_{day_idx}_{slot_idx}_{room}"
                        class_vars[(section, group, lab_name, teacher, day_idx, slot_idx, room)] = model.NewBoolVar(name)

# ----------------------------
# NEW: room-choice variables per lab subject
# For each lab_name we force solver to pick exactly one lab room for that lab subject.
# Then any lab class assigned for that lab must imply the chosen lab_room variable.
# ----------------------------
lab_room_choice = {}
for lab_name in LAB_NAMES:
    for room in LAB_ROOMS:
        v = model.NewBoolVar(f"lab_room_choice__{lab_name.replace(' ','_')}_{room}")
        lab_room_choice[(lab_name, room)] = v
    # exactly one room must be selected for this lab subject
    model.Add(sum(lab_room_choice[(lab_name, room)] for room in LAB_ROOMS) == 1)

# After creating class_vars we must link lab class vars to the lab_room_choice
# We will add implications var -> lab_room_choice[(lab_name, room)]
for (sec, grp, subj, tc, d, s, rm), var in list(class_vars.items()):
    if 'Lab' in subj:
        # subj is the lab name, rm is the room encoded in variable key
        # ensure that if var is true then the global choice for this lab_name equals rm
        if (subj, rm) in lab_room_choice:
            # add implication: var => lab_room_choice[(subj, rm)]
            model.AddImplication(var, lab_room_choice[(subj, rm)])
        else:
            # If subj found in LAB_NAMES but rm not in LAB_ROOMS (shouldn't happen), skip
            pass

# ----------------------------
# HARD CONSTRAINTS (existing)
# ----------------------------

# 1) A room can have only one class active at a time
for day_idx in range(len(DAYS)):
    for slot_idx in range(len(ALL_SLOTS)):
        for room in ALL_ROOMS:
            active = []
            for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
                if d != day_idx or rm != room:
                    continue
                # For theory: active if s == slot_idx
                # For lab: lab is 2-hour block starting at slot s -> active at s and s+1
                is_active = False
                if 'Lab' in subj:
                    # lab starts at slot s and occupies s and s+1
                    if s == slot_idx or s + 1 == slot_idx:
                        is_active = True
                else:
                    if s == slot_idx:
                        is_active = True
                if is_active:
                    active.append(var)
            if active:
                model.AddAtMostOne(active)

# 2) Teacher cannot teach more than one class at same time
for day_idx in range(len(DAYS)):
    for slot_idx in range(len(ALL_SLOTS)):
        for teacher in ALL_TEACHERS:
            active = []
            for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
                if d != day_idx or tc != teacher:
                    continue
                # check active as above
                if 'Lab' in subj:
                    if s == slot_idx or s + 1 == slot_idx:
                        active.append(var)
                else:
                    if s == slot_idx:
                        active.append(var)
            if active:
                model.AddAtMostOne(active)

# 3) Section (or group) can have only one class at a time
for section in SECTIONS:
    for group in GROUPS + ['ALL']:
        for day_idx in range(len(DAYS)):
            for slot_idx in range(len(ALL_SLOTS)):
                active = []
                for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
                    if sec != section or d != day_idx:
                        continue
                    is_relevant_group = (grp == group) or (group == 'ALL' and grp in GROUPS)
                    if not is_relevant_group:
                        continue
                    if 'Lab' in subj:
                        if s == slot_idx or s + 1 == slot_idx:
                            active.append(var)
                    else:
                        if s == slot_idx:
                            active.append(var)
                if active:
                    model.AddAtMostOne(active)

# 4) Each theory subject must be taught exactly 3 times a week (per section)
for section, section_subjects in SUBJECTS.items():
    for subject, teacher in section_subjects:
        vars_for_subject = [
            var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
            if sec == section and subj == subject and 'Lab' not in subj
        ]
        model.Add(sum(vars_for_subject) == 3)

# 5) Each lab for each group should be scheduled exactly once a week (this preserves lab counts)
for section, section_labs in LABS.items():
    for lab_name in section_labs:
        for group in GROUPS:
            vars_for_lab_group = [
                var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
                if sec == section and grp == group and subj == lab_name
            ]
            if vars_for_lab_group:
                model.Add(sum(vars_for_lab_group) == 1)

# 6) Recess rule: if teacher teaches 12-1 they cannot teach 2-3 same day
slot_12_1_idx = ALL_SLOTS.index("12-1")
slot_2_3_idx = ALL_SLOTS.index("2-3")
for teacher in ALL_TEACHERS:
    for day_idx in range(len(DAYS)):
        classes_at_12 = []
        classes_at_2 = []
        for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
            if tc != teacher or d != day_idx:
                continue
            # class occupies 12-1 if either starts at 12-1 (theory or lab starting at 12-1), or a lab starting at 11-12
            if 'Lab' in subj:
                # lab occupies s and s+1
                if s == slot_12_1_idx or s + 1 == slot_12_1_idx:
                    classes_at_12.append(var)
                if s == slot_2_3_idx or s + 1 == slot_2_3_idx:
                    classes_at_2.append(var)
            else:
                if s == slot_12_1_idx:
                    classes_at_12.append(var)
                if s == slot_2_3_idx:
                    classes_at_2.append(var)
        if classes_at_12:
            busy_at_12 = model.NewBoolVar(f"busy_{teacher}_{day_idx}_12")
            model.Add(sum(classes_at_12) > 0).OnlyEnforceIf(busy_at_12)
            model.Add(sum(classes_at_12) == 0).OnlyEnforceIf(busy_at_12.Not())
        else:
            busy_at_12 = None

        if classes_at_2:
            busy_at_2 = model.NewBoolVar(f"busy_{teacher}_{day_idx}_2")
            model.Add(sum(classes_at_2) > 0).OnlyEnforceIf(busy_at_2)
            model.Add(sum(classes_at_2) == 0).OnlyEnforceIf(busy_at_2.Not())
        else:
            busy_at_2 = None

        if busy_at_12 is not None and busy_at_2 is not None:
            model.AddBoolOr([busy_at_12.Not(), busy_at_2.Not()])

# 7) Each section: max 4 theory classes per day
for section in SECTIONS:
    for day_idx in range(len(DAYS)):
        daily_theory = [
            var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
            if sec == section and d == day_idx and 'Lab' not in subj
        ]
        model.Add(sum(daily_theory) <= 4)

# 8) For each section & group, max 2 labs per day (1 preferred, 2 allowed worst-case)
for section in SECTIONS:
    if section not in LABS:
        continue
    for group in GROUPS:
        for day_idx in range(len(DAYS)):
            labs_for_group_day = [
                var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
                if sec == section and grp == group and d == day_idx and 'Lab' in subj
            ]
            if labs_for_group_day:
                model.Add(sum(labs_for_group_day) <= 2)

# ----------------------------
# SOFT CONSTRAINTS / OBJECTIVE
# ----------------------------
# 1) Balance teacher daily load (minimize maximum daily load across teachers)
max_daily_load_vars = []
for teacher in ALL_TEACHERS:
    max_load = model.NewIntVar(0, len(ALL_SLOTS), f"max_load_{teacher}")
    daily_loads = []
    for day_idx in range(len(DAYS)):
        classes_on_day = []
        for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
            if tc == teacher and d == day_idx:
                classes_on_day.append(var)
        daily_loads.append(sum(classes_on_day))
    model.AddMaxEquality(max_load, daily_loads)
    max_daily_load_vars.append(max_load)

# 2) Prefer continuous theory blocks (minimize transitions)
continuity_penalties = []
for section in SECTIONS:
    for day_idx in range(len(DAYS)):
        is_theory_scheduled = {}
        for slot_idx in range(len(ALL_SLOTS)):
            b = model.NewBoolVar(f"is_theory_{section}_{day_idx}_{slot_idx}")
            theory_vars = [
                var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
                if sec == section and d == day_idx and s == slot_idx and 'Lab' not in subj
            ]
            if theory_vars:
                model.Add(sum(theory_vars) > 0).OnlyEnforceIf(b)
                model.Add(sum(theory_vars) == 0).OnlyEnforceIf(b.Not())
            else:
                model.Add(b == 0)
            is_theory_scheduled[slot_idx] = b

        for i in range(len(ALL_SLOTS) - 1):
            trans = model.NewBoolVar(f"trans_{section}_{day_idx}_{i}")
            model.Add(is_theory_scheduled[i] != is_theory_scheduled[i+1]).OnlyEnforceIf(trans)
            model.Add(is_theory_scheduled[i] == is_theory_scheduled[i+1]).OnlyEnforceIf(trans.Not())
            continuity_penalties.append(trans)

# 3) Prefer parallel labs (reward balanced group labs)
parallel_lab_penalties = []
for section in SECTIONS:
    if section not in LABS:
        continue
    for day_idx in range(len(DAYS)):
        for slot_idx, slot in enumerate(ALL_SLOTS):
            if slot not in LAB_SLOT_STARTS:
                continue
            group_a_labs = [
                var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
                if sec == section and grp == 'A' and d == day_idx and s == slot_idx and 'Lab' in subj
            ]
            group_b_labs = [
                var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
                if sec == section and grp == 'B' and d == day_idx and s == slot_idx and 'Lab' in subj
            ]
            gA = None
            gB = None
            if group_a_labs:
                gA = model.NewBoolVar(f"gA_has_{section}_{day_idx}_{slot_idx}")
                model.Add(sum(group_a_labs) > 0).OnlyEnforceIf(gA)
                model.Add(sum(group_a_labs) == 0).OnlyEnforceIf(gA.Not())
            if group_b_labs:
                gB = model.NewBoolVar(f"gB_has_{section}_{day_idx}_{slot_idx}")
                model.Add(sum(group_b_labs) > 0).OnlyEnforceIf(gB)
                model.Add(sum(group_b_labs) == 0).OnlyEnforceIf(gB.Not())

            if gA is not None and gB is not None:
                unbalanced = model.NewBoolVar(f"unbal_{section}_{day_idx}_{slot_idx}")
                model.Add(gA != gB).OnlyEnforceIf(unbalanced)
                model.Add(gA == gB).OnlyEnforceIf(unbalanced.Not())
                parallel_lab_penalties.append(unbalanced)

# 4) Prefer one lab per day per group (soft)
group_daily_lab_penalties = []
for section in SECTIONS:
    if section not in LABS:
        continue
    for group in GROUPS:
        for day_idx in range(len(DAYS)):
            labs_for_group_day = [
                var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
                if sec == section and grp == group and d == day_idx and 'Lab' in subj
            ]
            if not labs_for_group_day:
                continue
            pv = model.NewIntVar(0, len(LAB_SLOT_STARTS), f"group_lab_pen_{section}_{group}_{day_idx}")
            model.Add(pv >= sum(labs_for_group_day) - 1)
            group_daily_lab_penalties.append(pv)

# 5) Prefer one lab session per section per day (existing soft objective)
daily_lab_penalties = []
for section in SECTIONS:
    for day_idx in range(len(DAYS)):
        lab_session_helpers = []
        for slot_idx, slot in enumerate(ALL_SLOTS):
            if slot not in LAB_SLOT_STARTS:
                continue
            lab_at_slot = [
                var for (sec, grp, subj, tc, d, s, rm), var in class_vars.items()
                if sec == section and d == day_idx and s == slot_idx and 'Lab' in subj
            ]
            if not lab_at_slot:
                continue
            helper = model.NewBoolVar(f"lab_session_{section}_{day_idx}_{slot_idx}")
            model.Add(sum(lab_at_slot) > 0).OnlyEnforceIf(helper)
            model.Add(sum(lab_at_slot) == 0).OnlyEnforceIf(helper.Not())
            lab_session_helpers.append(helper)
        if lab_session_helpers:
            pv = model.NewIntVar(0, len(lab_session_helpers), f"lab_day_pen_{section}_{day_idx}")
            model.Add(pv >= sum(lab_session_helpers) - 1)
            daily_lab_penalties.append(pv)

# Combine objective weights
WORKLOAD_PENALTY_WEIGHT = 10
PARALLEL_LAB_PENALTY_WEIGHT = 8
DAILY_LAB_PENALTY_WEIGHT = 3
CONTINUITY_PENALTY_WEIGHT = 1
GROUP_DAILY_LAB_PENALTY_WEIGHT = 6

total_workload_penalty = sum(max_daily_load_vars)
total_continuity_penalty = sum(continuity_penalties)
total_parallel_lab_penalty = sum(parallel_lab_penalties)
total_daily_lab_penalty = sum(daily_lab_penalties)
total_group_lab_penalty = sum(group_daily_lab_penalties) if group_daily_lab_penalties else 0

model.Minimize(
    WORKLOAD_PENALTY_WEIGHT * total_workload_penalty +
    CONTINUITY_PENALTY_WEIGHT * total_continuity_penalty +
    PARALLEL_LAB_PENALTY_WEIGHT * total_parallel_lab_penalty +
    DAILY_LAB_PENALTY_WEIGHT * total_daily_lab_penalty +
    GROUP_DAILY_LAB_PENALTY_WEIGHT * total_group_lab_penalty
)

# ----------------------------
# SOLVE & EXPORT JSON (and Excel optionally)
# ----------------------------
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 180.0  # increase if needed
status = solver.Solve(model)

def make_entry(subj, teacher, room, is_lab, group=None):
    entry = {
        "teacher": teacher,
        "subject": subj,
        "room": room,
        "isLab": bool(is_lab)
    }
    if group:
        entry["group"] = group
    return entry

if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
    print("✅ Solution found — exporting JSON (and Excel if openpyxl available)...")

    # Build JSON structure
    output = {}
    for day_idx, day in enumerate(DAYS):
        day_list = []
        for section in SECTIONS:
            section_obj = {"section": section}
            # initialize empty lists for each slot
            for slot_idx, slot in enumerate(ALL_SLOTS):
                section_obj[slot] = []

            # iterate through class_vars to find active vars for this section/day
            for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
                if sec != section:
                    continue
                if d != day_idx:
                    continue
                if solver.Value(var):
                    # determine which slots this class occupies
                    if 'Lab' in subj:
                        # occupies starting slot s and s+1
                        start_slot_idx = s
                        if 0 <= start_slot_idx < len(ALL_SLOTS):
                            entry = make_entry(subj, tc, rm, True, grp if grp in GROUPS else None)
                            section_obj[ALL_SLOTS[start_slot_idx]].append(entry)
                            if start_slot_idx + 1 < len(ALL_SLOTS):
                                section_obj[ALL_SLOTS[start_slot_idx + 1]].append(entry.copy())
                    else:
                        # theory at slot s
                        slot_idx = s
                        if 0 <= slot_idx < len(ALL_SLOTS):
                            entry = make_entry(subj, tc, rm, False, None)
                            section_obj[ALL_SLOTS[slot_idx]].append(entry)

            day_list.append(section_obj)
        output[day] = day_list

    # write JSON
    json_path = "src/output/University_Master_Timetable.json"
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(output, jf, indent=2, ensure_ascii=False)
    print(f"✅ JSON exported to {json_path}")

else:
    print("❌ No feasible solution found.")
    print("Solver status:", solver.StatusName(status))
    print("Try relaxing constraints or increasing solver time.")
