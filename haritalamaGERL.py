import osmnx as ox  # OpenStreetMap verisi çekmece
import networkx as nx # yol to ag baglantı, noktalar to dugum,
import folium       #harita gösterim, görselleştirme
from folium.plugins import PolyLineTextPath  # Yön okları için eklendi
from geopy.distance import great_circle   # iki kordinat arası gerçek mesafe
from flask import Flask, render_template, request, jsonify, send_file # web arayuz
import json # json dosyası okuma
import os # dosya işlemleri kaydetme felan
import math 
from datetime import datetime, timedelta
import webbrowser

# Kavşak verilerini environment'dan oku
def load_intersections():
    try:
        # Önce environment'dan okumayı dene
        env_data = os.environ.get('INTERSECTION_DATA')
        if env_data:
            return json.loads(env_data)
        
        # Environment'da yoksa dosyadan oku (development için)
        with open('dataset.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Hata: {e}")
        return {}

# Uygulama başlangıcında verileri yükle
intersection_data = load_intersections()

# Flask uygulaması oluştur
app = Flask(__name__, template_folder='htmls')
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this")

# Basit önbellek 
class SimpleCache:
    def __init__(self):
        self.cache = {}
        
    def get(self, key):
        if key in self.cache:
            item, expiry = self.cache[key]
            if expiry is None or expiry > datetime.now():
                return item
            else:
                del self.cache[key]
        return None
        
    def set(self, key, value, timeout=None):
        expiry = None
        if timeout is not None:
            expiry = datetime.now() + timedelta(seconds=timeout)
        self.cache[key] = (value, expiry)
        
    def clear(self):
        self.cache.clear()

# Önbellek için
cache = SimpleCache()

# OSMnx ayarları
ox.settings.use_cache = True
ox.settings.log_console = True
ox.settings.default_crs = "EPSG:4326"

# Kavşak verileri
# intersection_data = [ 

# Global graf ve route değişkenleri
G = None
last_route = None
#G: Yol ağı grafı (osmnx ile çekiliyor). last_route: Son hesaplanan rotanın verileri (mesafe, süre, rota vs.)

#Ara durakları sıraya dizer (rota optimizasyonu)
def nearest_neighbor_order(G, intermediate_nodes, start_node, end_node, return_to_start=False, weight='length'):
    """Gelişmiş rota optimizasyon algoritması"""
    # Tekrar eden noktaları temizle
    unique_intermediate_nodes = list(dict.fromkeys(intermediate_nodes))
    
    # Hiç ara nokta yoksa basit bir rota döndür
    if not unique_intermediate_nodes:
        return [start_node, end_node] + ([start_node] if return_to_start else [])
    
    # Her bir düğüm arasındaki mesafe matrisini oluştur
    all_nodes = [start_node] + unique_intermediate_nodes + [end_node]
    distances = {}
    
    for i, node1 in enumerate(all_nodes):
        for node2 in all_nodes[i+1:]:
            try:
                path = nx.shortest_path(G, node1, node2, weight=weight)
                # Seçilen ağırlık tipine göre toplam ağırlığı hesapla
                dist = sum(G.edges[u, v, 0].get(weight, 0) for u, v in zip(path[:-1], path[1:]))
                distances[(node1, node2)] = dist
                distances[(node2, node1)] = dist  # Simetrik mesafe
            except:
                # Eğer iki düğüm arasında yol yoksa büyük bir değer ata
                distances[(node1, node2)] = float('inf')
                distances[(node2, node1)] = float('inf')
    
    # Coğrafi koordinatları al
    node_coords = {}
    for node in all_nodes:
        node_coords[node] = (G.nodes[node]['x'], G.nodes[node]['y'])
    
    # Düğümleri sırala
    if len(unique_intermediate_nodes) <= 3:
        # Az sayıda ara durak için tüm permütasyonları dene
        import itertools
        
        best_order = None
        best_distance = float('inf')
        
        for perm in itertools.permutations(unique_intermediate_nodes):
            order = [start_node] + list(perm) + [end_node]
            distance = sum(distances[(order[i], order[i+1])] for i in range(len(order)-1))
            
            if distance < best_distance:
                best_distance = distance
                best_order = order
                
        order = best_order
    else:
        # Daha fazla nokta için greedy algoritma kullan, ancak geometrik yön bilgisini ekle
        
        # Başlangıç, bitiş ve ara noktaların konumlarını al
        start_pos = node_coords[start_node]
        end_pos = node_coords[end_node]
        
        # İlerleme vektörünü hesapla (başlangıçtan hedefe doğru)
        direction_vector = (end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])
        direction_magnitude = math.sqrt(direction_vector[0]**2 + direction_vector[1]**2)
        
        if direction_magnitude > 0:
            direction_vector = (direction_vector[0]/direction_magnitude, direction_vector[1]/direction_magnitude)
        else:
            direction_vector = (0, 0)
        
        # Ara noktaları ilerleme vektörüne göre sırala
        def project_on_direction(node):
            node_vector = (node_coords[node][0] - start_pos[0], node_coords[node][1] - start_pos[1])
            return node_vector[0] * direction_vector[0] + node_vector[1] * direction_vector[1]
        
        # Ara noktaları yön projeksiyon değerine göre sırala
        sorted_intermediate = sorted(unique_intermediate_nodes, key=project_on_direction)
        
        # En yakın komşu ince ayar
        order = [start_node]
        remaining = sorted_intermediate.copy()
        
        current = start_node
        while remaining:
            closest = None
            min_dist = float('inf')
            
            for node in remaining:
                dist = distances.get((current, node), float('inf'))
                if dist < min_dist:
                    min_dist = dist
                    closest = node
            
            if closest is None:
                # Bağlantı bulunamadı, kalan noktaları atla
                break
            
            order.append(closest)
            remaining.remove(closest)
            current = closest
        
        order.append(end_node)
    
    # Eğer geri dönüş isteniyorsa başlangıç noktasını ekle
    if return_to_start:
        order.append(start_node)
    
    return order

#Bir rota düğümleri ile yolun gerçek geometrisini (kıvrımlar dahil):
def get_route_geometry(G, route):
    """Yüksek hassasiyetli yol geometrisi"""
    geom = []
    
    for u, v in zip(route[:-1], route[1:]):
        # Kenar verilerini al
        edge_data = None
        
        # Birden fazla kenar olabilir, en kısa olanı seç
        min_length = float('inf')
        for k in G[u][v]:
            edge = G[u][v][k]
            if 'length' in edge and edge['length'] < min_length:
                min_length = edge['length']
                edge_data = edge
        
        if edge_data is None:
            edge_data = G[u][v][0]  # varsayılan olarak ilk kenarı al
            
        # Geometri verisini işle
        if 'geometry' in edge_data:
            # LineString geometri verisi
            coords = list(edge_data['geometry'].coords)
            
            # Koordinatları ekle ve çiftleri önle
            if geom and geom[-1] == coords[0]:
                geom.extend(coords[1:])
            else:
                geom.extend(coords)
        else:
            # Geometri verisi yoksa düğüm koordinatlarını kullan
            start_coord = (G.nodes[u]['x'], G.nodes[u]['y'])
            end_coord = (G.nodes[v]['x'], G.nodes[v]['y'])
            
            # İlk noktayı ekle (eğer liste boş veya farklı bir nokta ise)
            if not geom or geom[-1] != start_coord:
                geom.append(start_coord)
            
            # Son noktayı ekle
            geom.append(end_coord)
    
    return geom

# Harita oluşturmaca rotayı çizer
def create_map(G, start_node, end_node, full_route, intermediate_coords, fuel_cost, return_trip, nodes_order):
    """Harita oluşturma işlevi"""
    m = folium.Map(location=[G.nodes[start_node]['y'], G.nodes[start_node]['x']], zoom_start=14)
    
    # Her segment için detaylı geometri al
    for i in range(len(nodes_order)-1):
        try:
            # İki düğüm arasındaki en kısa yolu bul
            segment = nx.shortest_path(G, nodes_order[i], nodes_order[i+1], weight='length')
            
            # Segmentin geometrisini al
            segment_geom = get_route_geometry(G, segment)
            
            # Son segment mor olsun (geri dönüş)
            if return_trip and i == len(nodes_order)-2:
                line_color = '#800080'
                line_weight = 4
                line_opacity = 0.7
            else:
                line_color = '#0066FF'
                line_weight = 6
                line_opacity = 0.8
            
            # Daha pürüzsüz ve doğru bir çizgi oluştur
            polyline = folium.PolyLine(
                [(y, x) for x, y in segment_geom],
                color=line_color,
                weight=line_weight,
                opacity=line_opacity,
                line_cap='round',
                line_join='round',
                tooltip='Geri Dönüş' if (return_trip and i == len(nodes_order)-2) else None
            )
            polyline.add_to(m)
            # Sadece ana rota (mavi çizgi) için yön okları ekle
            if not (return_trip and i == len(nodes_order)-2):
                # Ok karakteri: '➔' veya '▶' veya '→'
                PolyLineTextPath(
                    polyline,
                    '   ➔   ',
                    repeat=True,
                    offset=7,
                    attributes={
                        'fill': line_color,
                        'font-weight': 'bold',
                        'font-size': '18px',
                        'paint-order': 'stroke',
                        'stroke': 'white',
                        'stroke-width': '2px'
                    }
                ).add_to(m)
            
        except nx.NetworkXNoPath:
            # Direkt çizgi çiz
            start_pos = (G.nodes[nodes_order[i]]['y'], G.nodes[nodes_order[i]]['x'])
            end_pos = (G.nodes[nodes_order[i+1]]['y'], G.nodes[nodes_order[i+1]]['x'])
            
            folium.PolyLine(
                [start_pos, end_pos],
                color='#FF0000',  # Kırmızı renk (yol bulunamadı uyarısı)
                weight=3,
                opacity=0.6,
                line_cap='round',
                dash_array='5, 8',  # Kesikli çizgi
                tooltip='Yol bulunamadı - düz çizgi'
            ).add_to(m)
    
    # Başlangıç ve bitiş noktaları dışındaki düğümlerin sırasını belirle
    route_order = nodes_order[1:-1]  # Başlangıç ve bitiş hariç
    if return_trip:
        route_order = route_order[:-1]  # Geri dönüş noktasını da çıkar

    # Düğüm-koordinatları eşleştirme (waypoint'lerin (ara duraklar) sırasını bulabilmek için)
    node_to_coords = {}
    for node in route_order:
        node_to_coords[(G.nodes[node]['y'], G.nodes[node]['x'])] = node
    
    # Sıralı durakları göstermek için tüm noktaları listeye alıyoruz
    stop_points = []
    
    # Başlangıç noktası - numara yok
    start_point = {
        'lat': G.nodes[start_node]['y'],
        'lon': G.nodes[start_node]['x'],
        'name': 'Başlangıç',
        'seq': None, 
        'type': 'start'
    }
    stop_points.append(start_point)
    
    # Belirlenen rotaya göre ara durakları numaralandır
    waypoint_sequence = {}
    for seq_idx, node in enumerate(route_order, 1):
        node_lat = G.nodes[node]['y']
        node_lon = G.nodes[node]['x']
        
        # Bu düğüme en yakın ara durak noktasını bul
        min_dist = float('inf')
        closest_waypoint = None
        
        for idx, (lat, lon) in enumerate(intermediate_coords):
            dist = ((lat - node_lat) ** 2 + (lon - node_lon) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest_waypoint = idx
        
        # Eğer yeterince yakın bir ara durak bulunduysa, sıra numarasını kaydet
        if min_dist < 0.001:  # ~100 m yakınlıkta
            waypoint_sequence[closest_waypoint] = seq_idx
    
    # Ara durakları ekle - optimum rota sırasıyla
    for i, (lat, lon) in enumerate(intermediate_coords):
        # Rotadaki sıra numarası (varsa)
        seq_number = waypoint_sequence.get(i)
        
        waypoint = {
            'lat': lat,
            'lon': lon,
            'name': f'Ara Durak {i+1}',  # Orijinal waypoint numarası
            'seq': seq_number,  # Rotadaki sırası (None olabilir)
            'type': 'waypoint'
        }
        stop_points.append(waypoint)
    
    # Bitiş noktası - numara yok
    end_point = {
        'lat': G.nodes[end_node]['y'],
        'lon': G.nodes[end_node]['x'],
        'name': 'Bitiş',
        'seq': None,  # Numara yok
        'type': 'end'
    }
    stop_points.append(end_point)
    
    # Geri dönüş varsa başlangıç noktasını tekrar son durak olarak ekle - numara yok
    if return_trip:
        return_point = {
            'lat': G.nodes[start_node]['y'],
            'lon': G.nodes[start_node]['x'],
            'name': 'Dönüş Noktası',
            'seq': None,  # Numara yok
            'type': 'return'
        }
        stop_points.append(return_point)
    
    # Tüm noktaları işaretle
    for point in stop_points:
        # İkon rengini belirle
        if point['type'] == 'start':
            icon_color = 'green'
            icon_type = 'play'  # Başlangıç için yeni simge
        elif point['type'] == 'end':
            icon_color = 'red'
            icon_type = 'stop'  # Bitiş için yeni simge
        elif point['type'] == 'return':
            icon_color = 'purple'
            icon_type = 'home'
        else:
            icon_color = 'orange'
            icon_type = 'map-marker'
        
        # Sıra numarasına göre HTML içeriği
        if point['seq'] is not None:
            # Ara durak için numaralı ikon
            html_content = f"""
                <div style="position: relative; width: 40px; height: 40px;">
                    <i class="fa fa-{icon_type} fa-3x" style="color: {icon_color};"></i>
                    <div style="position: absolute; top: -5px; right: -5px; 
                              background-color: white; color: black; border-radius: 50%; 
                              width: 22px; height: 22px; display: flex; justify-content: center; 
                              align-items: center; font-weight: bold; font-size: 14px;
                              border: 2px solid {icon_color}; box-shadow: 0 0 3px rgba(0,0,0,0.3);">
                        {point['seq']}
                    </div>
                </div>
            """
            tooltip = f"{point['seq']}. {point['name']}"
        else:
            # Başlangıç veya bitiş için numarasız ikon
            html_content = f"""
                <div>
                    <i class="fa fa-{icon_type} fa-3x" style="color: {icon_color};"></i>
                </div>
            """
            tooltip = point['name']
        
        # Özel HTML içerikli ikon oluştur
        custom_icon = folium.DivIcon(
            html=html_content,
            icon_size=(40, 40),
            icon_anchor=(20, 40)
        )
        
        # Popup içeriği
        popup_content = f"<b>{point['name']}</b>"
        if point['seq'] is not None:
            popup_content += f"<br>Sıra: {point['seq']}"
        if point['type'] == 'start':
            popup_content += f"<br>Maliyet: {fuel_cost:.1f} TL"
        
        # İkonu haritaya ekle
        folium.Marker(
            [point['lat'], point['lon']],
            popup=popup_content,
            icon=custom_icon,
            tooltip=tooltip
        ).add_to(m)
    
    # Kavşak verilerini göster - diğer işaretlerden ayırmak için daha küçük ve şeffaf
    for intersection in intersection_data:
        icon_color = 'blue' if intersection['area'] == 5 else 'green'
        
        html_content = f"""
            <div style="opacity: 0.5;">
                <i class="fa fa-road fa-lg" style="color: {icon_color};"></i>
            </div>
        """
        
        intersection_icon = folium.DivIcon(
            html=html_content,
            icon_size=(20, 20),
            icon_anchor=(10, 10)
        )
        
        folium.Marker(
            [intersection['latitude'], intersection['longitude']],
            popup=f"<b>{intersection['intersection_name']}</b><br>ID: {intersection['intersection_id']}<br>Alan: {intersection['area']}",
            icon=intersection_icon,
            tooltip=intersection['intersection_name']
        ).add_to(m)
    
    # Haritayı HTML olarak döndür
    return m._repr_html_()

def get_cached_graph(place_name="Kayseri, Turkey", network_type='drive', timeout=3600):
    """Önbelleklenmiş harita grafiğini döndürür, yoksa yeni oluşturur."""
    cache_key = f"osm_graph_{place_name}_{network_type}"
    G = cache.get(cache_key)
    
    if G is None:
        G = ox.graph_from_place(place_name, network_type=network_type, simplify=False)
        
        # Yol hızları ve seyahat süreleri ekle
        try:
            G = ox.speed.add_edge_speeds(G)  # Sürüş hızlarını ekle
            G = ox.speed.add_edge_travel_times(G)  # Seyahat sürelerini hesapla
        except Exception as e:
            # Türkiye trafik yönetmeliğine göre hız değerleri
            for u, v, k, data in G.edges(keys=True, data=True):
                highway = data.get('highway', 'residential')
                if highway in ['motorway', 'motorway_link']:
                    speed = 120  # Otoyol
                elif highway in ['trunk', 'trunk_link']:
                    speed = 110  # Bölünmüş ana yol
                elif highway in ['primary', 'primary_link']:
                    speed = 90   # Ana yol
                elif highway in ['secondary', 'secondary_link']:
                    speed = 80   # İkincil yol
                elif highway in ['tertiary', 'tertiary_link']:
                    speed = 70   # Tali yol
                elif highway in ['residential', 'living_street']:
                    speed = 50   # Şehir içi
                elif highway in ['service', 'unclassified']:
                    speed = 30   # Servis ve sınıflandırılmamış yollar
                else:
                    speed = 50   # Varsayılan (şehir içi)
                # Eğer uzunluk bilgisi varsa, seyahat süresi hesapla
                if 'length' in data:
                    data['speed_kph'] = speed
                    data['travel_time'] = data['length'] / (speed / 3.6)  # km/s -> m/s için 3.6'ya böl
        
        # OSMNX 2.0+ sürümünde modül yapısı değişti, standart NetworkX fonksiyonlarını kullanıyoruz
        try:
            # Yolların açı bilgilerini ekle (daha düzgün dönüşler için)
            G = ox.bearing.add_edge_bearings(G)
        except Exception as e:
            pass
        
        # CRS uyarısını sustur
        import warnings
        warnings.filterwarnings('ignore', 'Geometry is in a geographic CRS')
        
        # Grafiği önbelleğe al
        cache.set(cache_key, G, timeout=timeout)
    return G

def calculate_route(start_lat, start_lon, end_lat, end_lon, intermediate_coords, fuel_cons, fuel_price, return_trip):
    """Rota hesaplama fonksiyonu - Sadece en kısa yol"""
    global G, last_route
    
    # Grafiği önbellekten al
    G = get_cached_graph()
    
    # En yakın düğümleri bul - nokta koordinatlarını yol ağında eşleştir
    start_node = ox.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.nearest_nodes(G, end_lon, end_lat)
    
    # intermediate_coords boş olduğunda hata oluşmasını önle
    if not intermediate_coords:
        intermediate_nodes = []
    else:
        try:
            intermediate_nodes = [ox.nearest_nodes(G, lon, lat) for lat, lon in intermediate_coords]
        except Exception as e:
            intermediate_nodes = []
    
    # En kısa yol için hesaplama yap
    weight = 'length'
    
    # Length olmayan kenarları kontrol et
    for u, v, k, data in G.edges(keys=True, data=True):
        if 'length' not in data:
            # Düğüm koordinatlarını al
            u_x, u_y = G.nodes[u].get('x', 0), G.nodes[u].get('y', 0)
            v_x, v_y = G.nodes[v].get('x', 0), G.nodes[v].get('y', 0)
            # Haversine mesafesini hesapla (metre cinsinden)
            dist = great_circle((u_y, u_x), (v_y, v_x)).meters
            data['length'] = dist
    
    # Rota optimizasyonu - ara durakları en verimli şekilde sırala
    nodes_order = nearest_neighbor_order(G, intermediate_nodes, start_node, end_node, return_trip, weight=weight)
    
    # Tüm rotayı oluştur - en kısa yol algoritması ile her segment için
    full_route = []
    for i in range(len(nodes_order)-1):
        try:
            # NetworkX'in Dijkstra algoritması ile segment hesapla
            segment = nx.shortest_path(G, nodes_order[i], nodes_order[i+1], weight=weight)
            # Segmenti ana rotaya ekle (ilk nokta hariç)
            full_route.extend(segment if not full_route else segment[1:])
        except nx.NetworkXNoPath:
            # Eğer iki nokta arasında doğrudan yol bulunamazsa
            # Alternatif yol bulma stratejisi (kuş uçuşu en yakın noktalara git)
            start_point = nodes_order[i]
            end_point = nodes_order[i+1]
            
            # Rotaya yerleştir
            if not full_route or full_route[-1] != start_point:
                full_route.append(start_point)
            full_route.append(end_point)
    
    # Mesafe hesaplaması
    total_distance = 0
    total_time = 0

    # Mesafe değerini kullan
    for i in range(len(full_route)-1):
        u, v = full_route[i], full_route[i+1]
        
        # Kenar verisi varsa
        if u in G and v in G[u]:
            # Birden fazla kenar varsa en kısa olanı seç
            min_length = float('inf')
            edge_data = None
            
            for k in G[u][v]:
                if 'length' in G[u][v][k] and G[u][v][k]['length'] < min_length:
                    min_length = G[u][v][k]['length']
                    edge_data = G[u][v][k]
            
            # Geçerli uzunluk bulunduysa kullan
            if min_length != float('inf'):
                distance_km = min_length / 1000  # km cinsinden
                total_distance += distance_km
                
                # Süreyi hesapla
                if edge_data and 'speed_kph' in edge_data:
                    speed = edge_data['speed_kph']
                else:
                    # Varsayılan hız (yol tipine göre)
                    speed = 50  # km/saat
                
                # Süreyi saniye olarak ekle: (mesafe/hız) * 3600
                time_seconds = (distance_km / speed) * 3600
                total_time += time_seconds
            else:
                # Length verisi yoksa koordinat bazlı hesapla
                start_pos = (G.nodes[u]['y'], G.nodes[u]['x'])
                end_pos = (G.nodes[v]['y'], G.nodes[v]['x'])
                dist_meters = great_circle(start_pos, end_pos).meters
                distance_km = dist_meters / 1000
                total_distance += distance_km
                
                # Varsayılan hızla süre hesapla
                time_seconds = (distance_km / 50) * 3600  # 50 km/saat varsayılan hız
                total_time += time_seconds
        
        # Kenar verisi yoksa koordinat bazlı hesapla
        else:
            start_pos = (G.nodes[u]['y'], G.nodes[u]['x'])
            end_pos = (G.nodes[v]['y'], G.nodes[v]['x'])
            dist_meters = great_circle(start_pos, end_pos).meters
            distance_km = dist_meters / 1000
            total_distance += distance_km
            
            # Varsayılan hızla süre hesapla
            time_seconds = (distance_km / 50) * 3600  # 50 km/saat varsayılan hız
            total_time += time_seconds
    
    # Maliyet hesaplamaları
    fuel_cost = (total_distance * fuel_cons / 100) * fuel_price

    # Harita oluştur
    map_html = create_map(G, start_node, end_node, full_route, intermediate_coords, 
                         fuel_cost, return_trip, nodes_order)

    # Zamanı biçimlendir (saat:dakika:saniye)
    hours = int(total_time / 3600)
    minutes = int((total_time % 3600) / 60)
    seconds = int(total_time % 60)
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"

    # Son rotayı kaydet
    last_route = {
        "full_route": full_route,
        "nodes_order": nodes_order,
        "total_km": total_distance,
        "total_time": total_time,
        "formatted_time": formatted_time,
        "fuel_cost": fuel_cost,
        "fuel_consumption": total_distance * fuel_cons / 100,
        "route_type": "shortest"
    }
    
    return {
        "map_html": map_html,
        "total_km": total_distance,
        "total_time": total_time,
        "formatted_time": formatted_time,
        "fuel_consumption": total_distance * fuel_cons / 100,
        "fuel_cost": fuel_cost,
        "route_type": "shortest"
    }

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html', intersections=intersection_data)

@app.route('/calculate', methods=['POST'])
def calculate():
    """Rota hesaplama API endpoint'i"""
    data = request.json
    
    start_lat = float(data['start_lat'])
    start_lon = float(data['start_lon'])
    end_lat = float(data['end_lat'])
    end_lon = float(data['end_lon'])
    intermediate_coords = data.get('intermediate_coords', [])
    fuel_cons = float(data['fuel_cons'])
    fuel_price = float(data['fuel_price'])
    return_trip = data.get('return_trip', False)
    
    try:
        result = calculate_route(
            start_lat, start_lon,
            end_lat, end_lon,
            intermediate_coords,
            fuel_cons, fuel_price,
            return_trip
        )
        return jsonify(result)
    except Exception as e:
        import traceback
        error_message = str(e)
        error_traceback = traceback.format_exc()
        return jsonify({"error": error_message}), 400

@app.route('/get_intersections')
def get_intersections():
    """Kavşak verilerini döndür"""
    return jsonify(intersection_data)

@app.route('/download_kml')
def download_kml():
    global last_route, G
    if last_route is None:
        return "Önce bir rota hesaplayın!", 400
    
    if G is None:
        return "Harita verisi yüklenmemiş!", 400
    
    # Rota verisinden GeoDataFrame oluştur
    try:
        # Detaylı geometriyi kullan
        route_nodes = last_route["full_route"]
        coords = get_route_geometry(G, route_nodes)
        if not coords:
            return "Rota koordinatları bulunamadı!", 400
        
        # LineString oluştur
        from shapely.geometry import LineString
        line = LineString(coords)
        
        # GeoDataFrame oluştur
        import geopandas as gpd
        # Yeni sürüm geopandas için doğrudan crs parametresi kullan
        gdf = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[line])
        
        # KML olarak kaydet
        kml_path = os.path.join(os.path.dirname(__file__), "static", "downloads")
        os.makedirs(kml_path, exist_ok=True)
        kml_file = os.path.join(kml_path, "kayseri_route.kml")
        
        gdf.to_file(kml_file, driver="KML")
        
        # Dosya adını anlamlı olacak şekilde değiştir
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_filename = f"kayseri_rota_{timestamp}.kml"
        
        return send_file(kml_file, as_attachment=True, download_name=download_filename)
        
    except Exception as e:
        import traceback
        error_message = str(e)
        error_traceback = traceback.format_exc()
        return f"KML dosyası oluşturulamadı: {error_message}", 500

if __name__ == "__main__":
    # Debug ve webbrowser.open kaldırılmalı
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)