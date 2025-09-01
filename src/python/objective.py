# objective.py

def set_objective(model, class_vars, config):
    """Defines the objective function to minimize penalties."""
    penalties = []
    
    # 1. Balance teacher daily load
    for teacher in config.ALL_TEACHERS:
        for day_idx in range(len(config.DAYS)):
            daily_load = sum(v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items() 
                             if tc == teacher and d == day_idx)
            penalties.append(daily_load * config.WEIGHTS['workload_penalty'])

    # 2. Prefer continuous theory blocks
    for section in config.SECTIONS:
        for day_idx in range(len(config.DAYS)):
            for i in range(len(config.ALL_SLOTS) - 1):
                theory_at_i = sum(v for (s, grp, subj, tc, d, s_idx, rm), v in class_vars.items() 
                                  if s == section and d == day_idx and s_idx == i and 'Lab' not in subj)
                theory_at_i1 = sum(v for (s, grp, subj, tc, d, s_idx, rm), v in class_vars.items() 
                                   if s == section and d == day_idx and s_idx == i + 1 and 'Lab' not in subj)
                
                is_theory_i = model.NewBoolVar('')
                model.Add(theory_at_i > 0).OnlyEnforceIf(is_theory_i)
                model.Add(theory_at_i == 0).OnlyEnforceIf(is_theory_i.Not())

                is_theory_i1 = model.NewBoolVar('')
                model.Add(theory_at_i1 > 0).OnlyEnforceIf(is_theory_i1)
                model.Add(theory_at_i1 == 0).OnlyEnforceIf(is_theory_i1.Not())

                transition = model.NewBoolVar('')
                model.Add(is_theory_i != is_theory_i1).OnlyEnforceIf(transition)
                model.Add(is_theory_i == is_theory_i1).OnlyEnforceIf(transition.Not())
                penalties.append(transition * config.WEIGHTS['continuity_penalty'])

    # 3. Prefer parallel labs
    for section in config.SECTIONS:
        for day_idx in range(len(config.DAYS)):
            for slot_idx, slot in enumerate(config.ALL_SLOTS):
                if slot not in config.LAB_SLOT_STARTS:
                    continue
                
                gA_active = model.NewBoolVar('')
                gB_active = model.NewBoolVar('')
                
                sum_gA = sum(v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items() 
                             if sec == section and grp == 'A' and d == day_idx and s == slot_idx)
                sum_gB = sum(v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items() 
                             if sec == section and grp == 'B' and d == day_idx and s == slot_idx)

                model.Add(sum_gA > 0).OnlyEnforceIf(gA_active)
                model.Add(sum_gA == 0).OnlyEnforceIf(gA_active.Not())
                model.Add(sum_gB > 0).OnlyEnforceIf(gB_active)
                model.Add(sum_gB == 0).OnlyEnforceIf(gB_active.Not())

                unbalanced = model.NewBoolVar('')
                model.Add(gA_active != gB_active).OnlyEnforceIf(unbalanced)
                model.Add(gA_active == gB_active).OnlyEnforceIf(unbalanced.Not())
                penalties.append(unbalanced * config.WEIGHTS['parallel_lab_penalty'])

    # 4 & 5. Penalize more than one lab session per day (for section and group)
    for section in config.SECTIONS:
        for day_idx in range(len(config.DAYS)):
            # Section penalty
            section_lab_sessions = []
            for slot_idx, slot in enumerate(config.ALL_SLOTS):
                if slot not in config.LAB_SLOT_STARTS:
                    continue
                session_active = model.NewBoolVar('')
                sum_labs = sum(v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items() 
                               if sec == section and d == day_idx and s == slot_idx)
                model.Add(sum_labs > 0).OnlyEnforceIf(session_active)
                model.Add(sum_labs == 0).OnlyEnforceIf(session_active.Not())
                section_lab_sessions.append(session_active)
            
            section_penalty = model.NewIntVar(0, 5, '')
            model.Add(section_penalty >= sum(section_lab_sessions) - 1)
            penalties.append(section_penalty * config.WEIGHTS['daily_lab_penalty'])
            
            # Group penalty
            for group in config.GROUPS:
                group_labs_today = sum(v for (sec, grp, subj, tc, d, s, rm), v in class_vars.items() 
                                       if sec == section and grp == group and d == day_idx)
                group_penalty = model.NewIntVar(0, 5, '')
                model.Add(group_penalty >= group_labs_today - 1)
                penalties.append(group_penalty * config.WEIGHTS['group_daily_lab_penalty'])
    
    # Final optimization objective
    model.Minimize(sum(penalties))
