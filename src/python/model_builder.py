# model_builder.py

def create_class_variables(model, config):
    """Creates boolean variables for every possible class session."""
    class_vars = {}
    
    # Theory class variables
    for section in config.SECTIONS:
        theory_room = config.SECTION_THEORY_ROOM.get(section)
        if not theory_room: continue
        for subject, teacher in config.SUBJECTS.get(section, []):
            for day_idx in range(len(config.DAYS)):
                for slot_idx in range(len(config.ALL_SLOTS)):
                    name = f"theory_{section}_{subject}_{day_idx}_{slot_idx}"
                    class_vars[(section, 'ALL', subject, teacher, day_idx, slot_idx, theory_room)] = model.NewBoolVar(name)
    
    # Lab variables
    for section in config.LABS:
        for lab_name in config.LABS.get(section, []):
            teacher = config.get_teacher_for_lab(section, lab_name)
            if not teacher: continue
            for group in config.GROUPS:
                for day_idx in range(len(config.DAYS)):
                    for slot_idx, slot in enumerate(config.ALL_SLOTS):
                        if slot not in config.LAB_SLOT_STARTS: continue
                        for room in config.LAB_ROOMS:
                            name = f"lab_{section}_{group}_{lab_name}_{day_idx}_{slot_idx}_{room}"
                            class_vars[(section, group, lab_name, teacher, day_idx, slot_idx, room)] = model.NewBoolVar(name)
    return class_vars

def create_and_link_lab_room_choices(model, class_vars, config):
    """Creates variables for assigning one room per lab subject and links them."""
    lab_room_choice = {}
    for lab_name in config.LAB_NAMES:
        choices = [model.NewBoolVar(f"lab_room_choice_{lab_name.replace(' ','_')}_{room}") for room in config.LAB_ROOMS]
        for i, room in enumerate(config.LAB_ROOMS):
            lab_room_choice[(lab_name, room)] = choices[i]
        model.AddExactlyOne(choices)

    # Link lab class variables to the global room choice
    for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
        if 'Lab' in subj and (subj, rm) in lab_room_choice:
            model.AddImplication(var, lab_room_choice[(subj, rm)])