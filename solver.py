# File: solver.py
import random

ITERATIONS, PERTURBATION_LEVEL = 2000, 3

def calculate_route_details(route, data):
    time_matrix, time_windows = data['travel_time_matrix'], {int(k): v for k, v in data['time_windows'].items()}
    service_time = data['service_time']
    current_time = 0
    for i in range(len(route) - 1):
        loc_from_id, loc_to_id = route[i], route[i+1]
        travel_time = time_matrix.get(loc_from_id, {}).get(loc_to_id, float('inf'))
        if travel_time == float('inf'): return False, float('inf')
        arrival_time = current_time + travel_time
        if arrival_time > time_windows[loc_to_id][1]: return False, float('inf')
        wait_time = max(0, time_windows[loc_to_id][0] - arrival_time)
        current_time = arrival_time + wait_time
        if loc_to_id in data['students']: current_time += service_time
    cost = sum(time_matrix.get(route[i], {}).get(route[i+1], float('inf')) for i in range(len(route) - 1))
    return True, cost

def refine_route_2opt(route, data):
    improved_route, has_improvement = route[:], True
    while has_improvement:
        has_improvement = False
        is_feasible, best_cost = calculate_route_details(improved_route, data)
        if not is_feasible: return improved_route
        for i in range(1, len(improved_route) - 2):
            for j in range(i + 1, len(improved_route) - 1):
                new_route = improved_route[:i] + improved_route[i:j+1][::-1] + improved_route[j+1:]
                is_feasible, new_cost = calculate_route_details(new_route, data)
                if is_feasible and new_cost < best_cost:
                    improved_route, best_cost, has_improvement = new_route, new_cost, True
                    break
            if has_improvement: break
    return improved_route

def perturb_route(route, level):
    perturbed_route = route[:]
    student_indices = list(range(1, len(perturbed_route) - 1))
    for _ in range(level):
        if len(student_indices) < 2: break
        i1, i2 = random.sample(student_indices, 2)
        perturbed_route[i1], perturbed_route[i2] = perturbed_route[i2], perturbed_route[i1]
    return perturbed_route

def solve(data, initial_route):
    if not initial_route: return None, float('inf')
    overall_best_route = refine_route_2opt(initial_route, data)
    is_feasible, overall_best_cost = calculate_route_details(overall_best_route, data)
    if not is_feasible: return None, float('inf')
    for _ in range(ITERATIONS):
        perturbed_route = perturb_route(overall_best_route, PERTURBATION_LEVEL)
        new_optimized_route = refine_route_2opt(perturbed_route, data)
        is_feasible, new_cost = calculate_route_details(new_optimized_route, data)
        if is_feasible and new_cost < overall_best_cost:
            overall_best_route, overall_best_cost = new_optimized_route, new_cost
    return overall_best_route, overall_best_cost

def build_initial_route(data):
    students_to_visit = set(data['students'].keys())
    garage, school = data['garage'], data['school']
    if not students_to_visit: return [garage, school]
    try:
        closest_student = min(students_to_visit, key=lambda s: data['travel_time_matrix'][garage].get(s, float('inf')))
    except ValueError:
        return [garage, school]
    route = [garage, closest_student, school]
    is_feasible, _ = calculate_route_details(route, data)
    if not is_feasible: return None
    students_to_visit.remove(closest_student)
    while students_to_visit:
        farthest_student = max(students_to_visit, key=lambda s: min(data['travel_time_matrix'][s].get(n, float('inf')) for n in route))
        best_pos, was_inserted = -1, False
        min_cost_increase = float('inf')
        for i in range(len(route) - 1):
            temp_route = route[:i+1] + [farthest_student] + route[i+1:]
            is_feasible, _ = calculate_route_details(temp_route, data)
            if is_feasible:
                cost_increase = (data['travel_time_matrix'][route[i]][farthest_student] + data['travel_time_matrix'][farthest_student][route[i+1]] - data['travel_time_matrix'][route[i]][route[i+1]])
                if cost_increase < min_cost_increase:
                    min_cost_increase, best_pos, was_inserted = cost_increase, i + 1, True
        if was_inserted:
            route.insert(best_pos, farthest_student); students_to_visit.remove(farthest_student)
        else:
            return None
    return route