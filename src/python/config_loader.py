# config_loader.py
import json

class Config:
    def __init__(self, data):
        self.data = data
        self._process_data()

    def _process_data(self):
        """Processes raw data to create derived lists like all teachers, rooms, etc."""
        self.DAYS = self.data['settings']['days']
        self.ALL_SLOTS = self.data['settings']['all_slots']
        self.LAB_SLOT_STARTS = self.data['settings']['lab_slot_starts']
        self.GROUPS = self.data['settings']['groups']
        self.SECTIONS = self.data['sections']
        self.LAB_ROOMS = self.data['lab_rooms']
        self.SUBJECTS = self.data['subjects']
        self.LABS = self.data['labs']
        self.SECTION_THEORY_ROOM = self.data['section_theory_rooms']
        self.WEIGHTS = self.data['objective_weights']
        
        # Derived properties
        self.ALL_TEACHERS = sorted(list(set(
            teacher for section_subjects in self.SUBJECTS.values() for _, teacher in section_subjects
        )))
        self.ALL_ROOMS = sorted(list(set(self.SECTION_THEORY_ROOM.values()) | set(self.LAB_ROOMS)))
        self.LAB_NAMES = sorted(list({lab for labs in self.LABS.values() for lab in labs}))

    def get_teacher_for_lab(self, section, lab_name):
        subject_name_map = {'Web Programming Lab': 'IWP', 'Artificial Intelligence Lab': 'AI', 'Seminar Lab': 'SM'}
        subject_name = subject_name_map.get(lab_name, lab_name.replace(' Lab', ''))
        for subject, teacher in self.SUBJECTS.get(section, []):
            if subject == subject_name:
                return teacher
        return None

def load_config(filepath="src/python/config.json"):
    """Loads the configuration from a JSON file and returns a Config object."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return Config(data)