import random
from typing import List, Dict, Tuple, Optional

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
PERIODS = 8 # 0-7

def run_backtracking_scheduler(teacher_availability: Dict[str, List[int]], courses: List[Dict]) -> Optional[List[Dict]]:
    """
    teacher_availability: {'Monday': [0,1,2], ...}
    courses: [{'id': 1, 'name': 'Math', 'hours': 3}, ...]
    returns: List of slots [{'day': 'Monday', 'period': 0, 'course_id': 1, 'subject': 'Math'}, ...]
    """
    tasks = []
    for c in courses:
        for _ in range(c['hours']):
            tasks.append({'id': c['id'], 'name': c['name']})
    
    # Shuffle tasks to get different results
    random.shuffle(tasks)
    
    timetable = []
    # Occupied slots for this specific generation: (day, period)
    occupied = set()

    def solve(task_idx):
        if task_idx == len(tasks):
            return True
        
        task = tasks[task_idx]
        
        # Try random days and periods
        available_slots = []
        for day in DAYS:
            for p in teacher_availability.get(day, []):
                if (day, p) not in occupied:
                    available_slots.append((day, p))
        
        random.shuffle(available_slots)
        
        for day, p in available_slots:
            occupied.add((day, p))
            timetable.append({
                'day': day,
                'period': p,
                'course_id': task['id'],
                'subject': task['name']
            })
            
            if solve(task_idx + 1):
                return True
            
            # Backtrack
            timetable.pop()
            occupied.remove((day, p))
            
        return False

    if solve(0):
        return timetable
    return None
