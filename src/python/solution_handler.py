# solution_handler.py
import json
from ortools.sat.python import cp_model

def export_solution(status, solver, class_vars, config):
    """Processes the solver result and writes the timetable to a JSON file."""
    if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
        print("✅ Solution found — exporting JSON...")
        
        output = {}
        for day_idx, day in enumerate(config.DAYS):
            day_list = []
            for section in config.SECTIONS:
                section_obj = {"section": section}
                for slot in config.ALL_SLOTS:
                    section_obj[slot] = []

                for (sec, grp, subj, tc, d, s, rm), var in class_vars.items():
                    if sec == section and d == day_idx and solver.Value(var):
                        entry = {
                            "teacher": tc, "subject": subj, "room": rm,
                            "isLab": 'Lab' in subj
                        }
                        if grp in config.GROUPS:
                            entry["group"] = grp
                        
                        start_slot_idx = s
                        section_obj[config.ALL_SLOTS[start_slot_idx]].append(entry)
                        if 'Lab' in subj and start_slot_idx + 1 < len(config.ALL_SLOTS):
                             section_obj[config.ALL_SLOTS[start_slot_idx + 1]].append(entry.copy())
                
                day_list.append(section_obj)
            output[day] = day_list
        
        # NOTE: Update this path to your desired output location
        json_path = "src/output/University_Master_Timetable.json"
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(output, jf, indent=2, ensure_ascii=False)
        print(f"✅ JSON exported to {json_path}")

    else:
        print("❌ No feasible solution found.")
        print("Solver status:", solver.StatusName(status))
        print("Try relaxing constraints or increasing solver time.")