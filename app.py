# File: app.py
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_executor import Executor
import osmnx as ox
import networkx as nx
import uuid
import random
from solver import solve, build_initial_route

# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_routes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
executor = Executor(app)
optimization_jobs = {}

# --- Database Models ---
class Garage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(200), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    route_type = db.Column(db.String(10), default='ida')
    schedule_time_min = db.Column(db.Integer)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    start_time_min = db.Column(db.Integer)
    end_time_min = db.Column(db.Integer)

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stop_order = db.Column(db.String(500))
    total_time = db.Column(db.Integer)
    itinerary = db.Column(db.JSON)
    route_geometry = db.Column(db.JSON)

# --- Helper Functions ---
def geocode_address(address):
    try:
        location = ox.geocode(f"{address}, São Bento do Sul, SC, Brazil")
        return location[0], location[1]
    except: return None, None

def time_to_minutes(time_str):
    if not time_str: return None
    try: h, m = map(int, time_str.split(':')); return h * 60 + m
    except: return None

def minutes_to_time(minutes):
    if minutes is None: return ''
    h, m = divmod(int(minutes), 60); return f"{h:02d}:{m:02d}"

FIRST_NAMES = ["Lucas", "Sofia", "Mateus", "Júlia", "Guilherme", "Isabella", "Pedro", "Laura", "Bernardo", "Alice"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes"]

# --- Web Routes ---
@app.route('/')
def index():
    with app.app_context():
        db.create_all()
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    garage, school, students, route = Garage.query.first(), School.query.first(), Student.query.all(), Route.query.first()
    return jsonify({
        'garage': {'id': garage.id, 'address': garage.address, 'lat': garage.lat, 'lon': garage.lon} if garage else None,
        'school': {
            'id': school.id, 'name': school.name, 'address': school.address, 'lat': school.lat, 'lon': school.lon,
            'route_type': school.route_type,
            'schedule_time': minutes_to_time(school.schedule_time_min)
        } if school else None,
        'students': [{
            'id': s.id, 'name': s.name, 'address': s.address, 'lat': s.lat, 'lon': s.lon,
            'start_time': minutes_to_time(s.start_time_min),
            'end_time': minutes_to_time(s.end_time_min)
        } for s in students],
        'route': {'itinerary': route.itinerary, 'total_time': route.total_time, 'geometry': route.route_geometry} if route else None
    })

@app.route('/api/location', methods=['POST'])
def add_location():
    data = request.json
    address = data.get('address')
    if not address: return jsonify(success=False, message="Endereço é obrigatório."), 400
    
    lat, lon = geocode_address(address)
    if lat is None: return jsonify(success=False, message=f"Endereço não encontrado: {address}"), 400
    
    loc_type = data.get('type')
    if loc_type == 'garage':
        Garage.query.delete()
        new_loc = Garage(address=address, lat=lat, lon=lon)
    elif loc_type == 'school':
        School.query.delete()
        schedule_time_min = time_to_minutes(data.get('schedule_time'))
        route_type = data.get('route_type', 'ida')
        new_loc = School(name=data.get('name'), address=address, lat=lat, lon=lon, schedule_time_min=schedule_time_min, route_type=route_type)
    elif loc_type == 'student':
        start_time_min = time_to_minutes(data.get('start_time'))
        end_time_min = time_to_minutes(data.get('end_time'))
        new_loc = Student(name=data.get('name'), address=address, lat=lat, lon=lon, start_time_min=start_time_min, end_time_min=end_time_min)
    else:
        return jsonify(success=False, message="Tipo inválido"), 400
        
    db.session.add(new_loc)
    db.session.commit()
    return jsonify(success=True, message=f"{loc_type.capitalize()} adicionado!")

@app.route('/api/add_random_students', methods=['POST'])
def add_random_students():
    school = School.query.first()
    if not school: return jsonify(success=False, message="Cadastre uma escola primeiro para definir a região."), 400
    
    num_to_add = request.json.get('count', 10)
    lat_offset, lon_offset = 0.01125, 0.01375 
    
    for _ in range(num_to_add):
        random_lat = school.lat + random.uniform(-lat_offset, lat_offset)
        random_lon = school.lon + random.uniform(-lon_offset, lon_offset)
        
        # --- LÓGICA ATUALIZADA PARA JANELAS ENTRE 06:15 E 08:30 ---
        EARLIEST_START_MINUTE = 375  # 06:15
        LATEST_END_MINUTE = 510      # 08:30
        MIN_DURATION = 30
        MAX_DURATION = 75

        # O horário de início é sorteado para permitir que a janela termine até as 8:30
        latest_possible_start = LATEST_END_MINUTE - MIN_DURATION
        start_min = random.randint(EARLIEST_START_MINUTE, latest_possible_start)
        
        # A duração é sorteada
        duration_min = random.randint(MIN_DURATION, MAX_DURATION)
        
        # O horário final é calculado e limitado para não passar do horário final geral
        end_min = min(start_min + duration_min, LATEST_END_MINUTE)
        # ----------------------------------------------------------------

        student = Student(
            name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            address="Local Aleatório",
            lat=random_lat, lon=random_lon,
            start_time_min=start_min, end_time_min=end_min
        )
        db.session.add(student)
        
    db.session.commit()
    return jsonify(success=True, message=f"{num_to_add} alunos aleatórios adicionados!")

@app.route('/api/location/<loc_type>/<int:loc_id>', methods=['DELETE'])
def delete_location(loc_type, loc_id):
    if loc_type == 'student': item = Student.query.get_or_404(loc_id)
    elif loc_type == 'school': item = School.query.get_or_404(loc_id)
    elif loc_type == 'garage': item = Garage.query.get_or_404(loc_id)
    else: return jsonify(success=False), 400
    db.session.delete(item); db.session.commit()
    return jsonify(success=True)

# --- Background Task ---
def run_optimization_background(job_id):
    with app.app_context():
        try:
            garage, school, students = Garage.query.first(), School.query.first(), Student.query.all()
            if not all([garage, school, students]): raise ValueError("Dados insuficientes (garagem, escola e ao menos um aluno são necessários).")
            if not school.schedule_time_min: raise ValueError("A escola precisa de um horário definido.")
            
            garage_node_id, school_node_id = -1, 0
            
            locations = {garage_node_id: (garage.lat, garage.lon), school_node_id: (school.lat, school.lon)}
            student_map = {s.id: (s.lat, s.lon) for s in students}
            locations.update(student_map)
            center_point = (school.lat, school.lon)
            G = ox.graph_from_point(center_point, dist=10000, network_type='drive')
            location_nodes = {id: ox.distance.nearest_nodes(G, lon, lat) for id, (lat, lon) in locations.items()}
            
            time_matrix = {from_id: {to_id: 0 for to_id in locations} for from_id in locations}
            for from_id in locations:
                for to_id in locations:
                    if from_id == to_id: continue
                    try:
                        length = nx.shortest_path_length(G, location_nodes[from_id], location_nodes[to_id], weight='length')
                        time_matrix[from_id][to_id] = round((length / 1000) / 25 * 60)
                    except nx.NetworkXNoPath: time_matrix[from_id][to_id] = float('inf')

            problem_data = { "students": {s.id: () for s in students}, "travel_time_matrix": time_matrix, "service_time": 1 }
            time_windows = {}

            if school.route_type == 'ida':
                problem_data.update({"garage": garage_node_id, "school": school_node_id})
                time_windows[str(garage_node_id)] = [0, 1440]
                time_windows[str(school_node_id)] = [0, school.schedule_time_min]
                for s in students: time_windows[str(s.id)] = [s.start_time_min, s.end_time_min]
            
            elif school.route_type == 'volta':
                problem_data.update({"garage": school_node_id, "school": garage_node_id})
                time_windows[str(school_node_id)] = [school.schedule_time_min, 1440]
                time_windows[str(garage_node_id)] = [0, 1440]
                for s in students: time_windows[str(s.id)] = [school.schedule_time_min, 1440]

            problem_data["time_windows"] = time_windows
            
            initial_route = build_initial_route(problem_data)
            if not initial_route: raise ValueError("Não foi possível construir uma rota inicial viável com as restrições de tempo.")

            final_route, final_cost = solve(problem_data, initial_route)
            
            Route.query.delete()
            if final_route and final_cost != float('inf'):
                itinerary = []
                current_time = problem_data['time_windows'][str(final_route[0])][0]

                for i, stop_id in enumerate(final_route):
                    if i > 0:
                        arrival_time = current_time + time_matrix[final_route[i-1]][stop_id]
                        wait_time = max(0, problem_data['time_windows'][str(stop_id)][0] - arrival_time)
                        current_time = arrival_time + wait_time
                    
                    stop_time = minutes_to_time(current_time)
                    
                    if stop_id == school_node_id: itinerary.append({'type': 'Escola', 'name': school.name, 'time': stop_time})
                    elif stop_id == garage_node_id: itinerary.append({'type': 'Garagem', 'name': 'Garagem', 'time': stop_time})
                    else: itinerary.append({'type': 'Aluno', 'name': Student.query.get(stop_id).name, 'time': stop_time})
                    
                    if stop_id in student_map: current_time += problem_data['service_time']
                
                route_geometry = []
                for i in range(len(final_route) - 1):
                    start_node = location_nodes[final_route[i]]; end_node = location_nodes[final_route[i+1]]
                    path_nodes = nx.shortest_path(G, start_node, end_node, weight='length')
                    route_geometry.append([[G.nodes[node]['y'], G.nodes[node]['x']] for node in path_nodes])
                
                db.session.add(Route(stop_order=",".join(map(str, final_route)), total_time=int(final_cost), itinerary=itinerary, route_geometry=route_geometry))
                db.session.commit()
                optimization_jobs[job_id]['status'] = 'complete'; optimization_jobs[job_id]['message'] = f"Rota otimizada com tempo de viagem de {int(final_cost)} min!"
            else:
                raise ValueError("O solver não conseguiu encontrar uma rota viável.")
        except Exception as e:
            db.session.rollback(); optimization_jobs[job_id]['status'] = 'failed'; optimization_jobs[job_id]['message'] = str(e)

@app.route('/api/optimize', methods=['POST'])
def optimize():
    job_id = str(uuid.uuid4())
    optimization_jobs[job_id] = {'status': 'running', 'message': 'Otimização iniciada...'}
    executor.submit(run_optimization_background, job_id)
    return jsonify(success=True, job_id=job_id)

@app.route('/api/optimize/status/<job_id>')
def optimization_status(job_id):
    return jsonify(optimization_jobs.get(job_id, {'status': 'unknown'}))

if __name__ == '__main__':
    app.run(debug=True)