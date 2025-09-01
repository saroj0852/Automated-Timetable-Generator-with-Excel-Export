# main.py
from ortools.sat.python import cp_model
import config_loader
import model_builder
import constraints
import objective
import solution_handler

def main():
    """Main function to generate the timetable."""
    print("🚀 Starting timetable generation process...")

    # 1. Load configuration from JSON
    config = config_loader.load_config("src/python/config.json")
    print("   - Configuration loaded from config.json.")

    # 2. Create the model and variables
    model = cp_model.CpModel()
    class_vars = model_builder.create_class_variables(model, config)
    model_builder.create_and_link_lab_room_choices(model, class_vars, config)
    print(f"   - Created {len(class_vars)} decision variables.")

    # 3. Add all hard constraints
    constraints.add_hard_constraints(model, class_vars, config)
    print("   - Hard constraints added.")

    # 4. Set the objective function (pass class_vars + config properly)
    objective.set_objective(model, class_vars, config)
    print("   - Objective function set.")

    # 5. Solve the model
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(config.data['settings']['solver_timeout_seconds'])
    print(f"   - Solver is running (max {solver.parameters.max_time_in_seconds} seconds)...")
    status = solver.Solve(model)

    # 6. Process and export the solution
    solution_handler.export_solution(status, solver, class_vars, config)
    print("✨ Process complete.")

if __name__ == "__main__":
    main()
