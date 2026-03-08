import heapq
import random
import math
import matplotlib.pyplot as plt
import networkx as nx
random.seed(42)
SPEED_OF_LIGHT=3e8


# -------------------------------------------------
# SATELLITE NETWORK MODEL
# -------------------------------------------------

def create_satellite_network():
    return {
        "Ground_Station_1": {
            "LEO_Sat": {"distance_km": 500}
        },
        "LEO_Sat": {
            "Ground_Station_1": {"distance_km": 500},
            "MEO_Sat": {"distance_km": 8000}
        },
        "MEO_Sat": {
            "LEO_Sat": {"distance_km": 8000},
            "GEO_Sat": {"distance_km": 20000}
        },
        "GEO_Sat": {
            "MEO_Sat": {"distance_km": 20000},
            "Ground_Station_2": {"distance_km": 36000}
        },
        "Ground_Station_2": {
            "GEO_Sat": {"distance_km": 36000}
        }
    }

graph = create_satellite_network()

# -------------------------------------------------
# COMMUNICATION FORMULAS
# -------------------------------------------------

def free_space_path_loss(distance_km, frequency_mhz):
    return 20 * math.log10(distance_km) + 20 * math.log10(frequency_mhz) + 32.44
def calculate_snr(fspl):

    signal_power = 100   # satellite transmit power
    noise_power = random.uniform(1,10)

    snr = signal_power / (noise_power + fspl/100)

    return snr
def calculate_ber(snr):

    ber = 1 / (1 + snr)

    return ber

def rain_attenuation():
    rain_intensity = random.uniform(0, 50)  # mm/hr
    attenuation = rain_intensity * 0.02

    # Heavy rain condition
    if rain_intensity > 40:
        return attenuation, True   # Failure possible

    return attenuation, False

def dynamic_distance(node1, node2, base_distance):

    # LEO satellites move fast → more variation
    if "LEO" in node1 or "LEO" in node2:
        variation = random.uniform(-100, 100)

    # MEO medium variation
    elif "MEO" in node1 or "MEO" in node2:
        variation = random.uniform(-50, 50)

    # GEO almost stable
    elif "GEO" in node1 or "GEO" in node2:
        variation = random.uniform(-10, 10)

    else:
        variation = random.uniform(-20, 20)

    return max(1, base_distance + variation)
def power_constraint():

    available_power = random.uniform(50, 100)   # available satellite power
    required_power = random.uniform(40, 90)    # required transmission power

    if required_power > available_power:
        return False   # Power insufficient

    return True
# -------------------------------------------------
# RANDOM LINK FAILURE MODEL
# -------------------------------------------------

def link_failure():

    failure_probability = 0.1   # 10% failure chance

    if random.random() < failure_probability:
        return True

    return False
# -------------------------------------------------
# ORBITAL MOTION MODEL (Physics-Based)
# -------------------------------------------------

def orbital_distance(node1, node2, base_distance, time):

    # LEO → Fast sinusoidal variation
    if "LEO" in node1 or "LEO" in node2:
        return base_distance + 100 * math.sin(time)

    # MEO → Medium variation
    elif "MEO" in node1 or "MEO" in node2:
        return base_distance + 50 * math.sin(time / 2)

    # GEO → Almost constant
    elif "GEO" in node1 or "GEO" in node2:
        return base_distance

    else:
        return base_distance
# -------------------------------------------------
# DIJKSTRA WITH FSPL + RAIN
# -------------------------------------------------

def find_path(graph, start, end, frequency,time):

    queue = [(0, start)]
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous = {}

    while queue:
        current_distance, current_node = heapq.heappop(queue)

        for neighbor, params in graph[current_node].items():

            base_d = params["distance_km"]
            d = orbital_distance(current_node, neighbor, base_d,time)

            fspl = free_space_path_loss(d, frequency)
            snr = calculate_snr(fspl)

            if snr < 1:   # low signal quality
               continue
            rain_loss, rain_failure = rain_attenuation()

            if rain_failure or link_failure():
               continue
            # Power availability check
            if not power_constraint():
               continue
            total_weight = fspl + rain_loss

            distance = current_distance + total_weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous[neighbor] = current_node
                heapq.heappush(queue, (distance, neighbor))

    path = []
    node = end
    while node in previous:
        path.insert(0, node)
        node = previous[node]
    path.insert(0, start)

    return path

# -------------------------------------------------
# PERFORMANCE METRICS
# -------------------------------------------------

# -------------------------------------------------
# PHYSICS-BASED PROPAGATION DELAY
# -------------------------------------------------

def calculate_delay(path, graph, time):

    total_delay = 0

    for i in range(len(path)-1):

        node1 = path[i]
        node2 = path[i+1]

        base_distance = graph[node1][node2]["distance_km"]

        # Use orbital motion distance
        distance_km = orbital_distance(node1, node2, base_distance, time)

        distance_m = distance_km * 1000  # convert km to meters

        propagation_delay = distance_m / SPEED_OF_LIGHT  # seconds

        total_delay += propagation_delay

    return total_delay * 1000  # convert to milliseconds

def calculate_throughput(delay_ms):

    base_bandwidth = 1000   # Mbps (Max satellite bandwidth)

    # Network congestion factor (traffic load)
    congestion_factor = random.uniform(0.4, 1)

    effective_bandwidth = base_bandwidth * congestion_factor

    # Throughput affected by delay also
    throughput = effective_bandwidth / (1 + delay_ms/100)

    return throughput
successful_transmissions = 0
failed_transmissions = 0


# -------------------------------------------------
# STATISTICAL SIMULATION
# -------------------------------------------------

cycles = 100
frequency_mhz = 2000  # 2 GHz satellite link

packet_loss_list = []
throughput_list = []
delay_list = []
reliability_list=[]
ber_list=[]

print("Satellite Self-Healing Communication Simulation Started")

for cycle in range(cycles):

    path = find_path(graph, "Ground_Station_1",
                     "Ground_Station_2",
                     frequency_mhz,
                     cycle)
    if path and path[-1] == "Ground_Station_2":
       print("Cycle:", cycle, "Path:", path)
    else:
       print("Cycle:", cycle, "Path: FAILED")

    # If path not found → failure
    if not path or path[-1] !="Ground_Station_2":
        failed_transmissions += 1
        continue

    # If path exists → success
    successful_transmissions += 1

    delay = calculate_delay(path, graph, cycle)
    throughput = calculate_throughput(delay)
    snr=calculate_snr(delay)
    ber=calculate_ber(snr)
    packet_loss = random.uniform(0,5)+(delay/200)

    packet_loss_list.append(packet_loss)
    throughput_list.append(throughput)
    delay_list.append(delay)
    reliability = 100 - packet_loss
    reliability_list.append(reliability)
    ber_list.append(ber)
    
    
    

    

# -------------------------------------------------
# STATISTICAL RESULTS
# -------------------------------------------------

if successful_transmissions > 0:
    avg_delay = sum(delay_list) / successful_transmissions
    avg_throughput = sum(throughput_list) / successful_transmissions
    avg_packet_loss = sum(packet_loss_list) / successful_transmissions
else:
    avg_delay = avg_throughput = avg_packet_loss = 0
    
reliability = 100 - avg_packet_loss

print("\n----- STATISTICAL RESULTS -----")
print("Average Delay (ms):", round(avg_delay,2))
print("Average Throughput (Mbps):", round(avg_throughput,2))
print("Average Packet Loss (%):", round(avg_packet_loss,2))
print("Network Reliability (%):", round(reliability,2))
availability = (successful_transmissions / cycles) * 100

print("Network Availability (%):", round(availability,2))
# -------------------------------------------------
# SATELLITE NETWORK TOPOLOGY GRAPH
# -------------------------------------------------

G = nx.Graph()

for node in graph:
    for neighbor in graph[node]:
        if not G.has_edge(node,neighbor):
           G.add_edge(node, neighbor)

plt.figure(figsize=(6,4))
pos = nx.spring_layout(G)

nx.draw(G, pos, with_labels=True, node_size=2000)

plt.title("Satellite Communication Network Topology")
plt.show()

# -------------------------------------------------
# PROFESSIONAL RESEARCH STYLE SEPARATE GRAPHS
# -------------------------------------------------

# --------- 1️⃣ DELAY GRAPH ---------
plt.figure(figsize=(6,4))
plt.plot(delay_list,marker='o')
plt.axhline(avg_delay, linestyle='--')
plt.title("Propagation Delay vs Simulation Cycle")
plt.xlabel("Cycle")
plt.ylabel("Delay (ms)")
plt.grid(True)
plt.tight_layout()
plt.savefig("delay_graph.png", dpi=300)
plt.show()


# --------- 2️⃣ THROUGHPUT GRAPH ---------
plt.figure(figsize=(6,4))
plt.plot(throughput_list,marker='o')
plt.axhline(avg_throughput, linestyle='--')
plt.title("Throughput vs Simulation Cycle")
plt.xlabel("Cycle")
plt.ylabel("Throughput (Mbps)")
plt.grid(True)
plt.tight_layout()
plt.savefig("throughput_graph.png", dpi=300)
plt.show()


# --------- 3️⃣ PACKET LOSS GRAPH ---------
plt.figure(figsize=(6,4))
plt.plot(packet_loss_list,marker='o')
plt.axhline(avg_packet_loss, linestyle='--')
plt.title("Packet Loss vs Simulation Cycle")
plt.xlabel("Cycle")
plt.ylabel("Packet Loss (%)")
plt.grid(True)
plt.tight_layout()
plt.savefig("packet_loss_graph.png", dpi=300)
plt.show()
# --------- 4️⃣ RELIABILITY GRAPH ---------
plt.figure(figsize=(6,4))
plt.plot(reliability_list,marker='o')
plt.title("Network Reliability vs Simulation Cycle")
plt.xlabel("Cycle")
plt.ylabel("Reliability (%)")
plt.grid(True)
plt.tight_layout()
plt.savefig("reliability_graph.png", dpi=300)
plt.show()

plt.figure(figsize=(6,4))
plt.plot(ber_list,marker='o')
plt.title("Bit Error Rate vs Simulation Cycle")
plt.xlabel("Cycle")
plt.ylabel("BER")
plt.grid(True)
plt.show()
