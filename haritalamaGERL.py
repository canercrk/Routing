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

# Flask uygulaması oluştur
app = Flask(__name__, template_folder='htmls')

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
intersection_data = [
    {"intersection_id": 3, "intersection_name": "TUNA KAVŞAĞI", "latitude": 38.74078, "longitude": 35.5155, "area": 5},
    {"intersection_id": 5, "intersection_name": "FUZULI KAVŞAĞI", "latitude": 38.73718, "longitude": 35.50397, "area": 5},
    {"intersection_id": 7, "intersection_name": "İSTASYON", "latitude": 38.73068, "longitude": 35.48264, "area": 5},
    {"intersection_id": 8, "intersection_name": "GAR", "latitude": 38.72937, "longitude": 35.47848, "area": 5},
    {"intersection_id": 9, "intersection_name": "OYMAK CD. BALKIRAZ CD.", "latitude": 38.73814, "longitude": 35.46887, "area": 5},
    {"intersection_id": 43, "intersection_name": "YAVUZ SULTAN SELIM CD.- ORHAN GAZI CD ( ARGINCIK MEYDAN)", "latitude": 38.7498, "longitude": 35.5158, "area": 5},
    {"intersection_id": 45, "intersection_name": "ADLİYE", "latitude": 38.73546, "longitude": 35.47982, "area": 5},
    {"intersection_id": 47, "intersection_name": "KALDIRIM CD. - BAGDAT CD. ( GAZI OSMAN )", "latitude": 38.73186, "longitude": 35.46937, "area": 5},
    {"intersection_id": 51, "intersection_name": "YEŞİL MAHALLE MEYDAN", "latitude": 38.75546, "longitude": 35.46796, "area": 5},
    {"intersection_id": 55, "intersection_name": "DOĞUMEVİ YAYA", "latitude": 38.73977, "longitude": 35.49115, "area": 5},
    {"intersection_id": 57, "intersection_name": "12.CD. - 5.CD. ( YENI MAHALLE MEYDAN ) FLAS", "latitude": 38.74243, "longitude": 35.48386, "area": 5},
    {"intersection_id": 59, "intersection_name": "EMNİYET KAVŞAĞI", "latitude": 38.73993, "longitude": 35.47715, "area": 5},
    {"intersection_id": 64, "intersection_name": "KAYSERİ PARK", "latitude": 38.72806, "longitude": 35.51883, "area": 3},
    {"intersection_id": 65, "intersection_name": "FUZULI CD. - BOZANTI CD. ( FLASLAR )", "latitude": 38.73634, "longitude": 35.50443, "area": 5},
    {"intersection_id": 69, "intersection_name": "BARIS MANÇO CAD. - 3540. SOKAK ( MEVLANA)", "latitude": 38.73693, "longitude": 35.48378, "area": 5},
    {"intersection_id": 72, "intersection_name": "KIZILIRMAK-AŞIKVEYSEL", "latitude": 38.72982, "longitude": 35.52482, "area": 3},
    {"intersection_id": 73, "intersection_name": "BAGDAT CD. LIMAN CD. ( FLASLAR )", "latitude": 38.73618, "longitude": 35.46425, "area": 5},
    {"intersection_id": 75, "intersection_name": "75.YIL", "latitude": 38.75005, "longitude": 35.48612, "area": 5},
    {"intersection_id": 82, "intersection_name": "AŞIKVEYSEL- MUSTAFA ŞİMŞEK", "latitude": 38.72777, "longitude": 35.52567, "area": 3},
    {"intersection_id": 84, "intersection_name": "AŞIKVEYSEL-FAKÜLTE İÇİ", "latitude": 38.70864, "longitude": 35.53083, "area": 3},
    {"intersection_id": 85, "intersection_name": "ARGINCIK TOPTANCILAR", "latitude": 38.74471, "longitude": 35.51247, "area": 5},
    {"intersection_id": 94, "intersection_name": "GARNİZON KAVŞAĞI", "latitude": 38.70817, "longitude": 35.50673, "area": 3},
    {"intersection_id": 96, "intersection_name": "MAYA GÖZ KAVŞAĞI", "latitude": 38.70495, "longitude": 35.51294, "area": 3},
    {"intersection_id": 98, "intersection_name": "İLAHİYAT KAVŞAĞI", "latitude": 38.70286, "longitude": 35.51701, "area": 3},
    {"intersection_id": 100, "intersection_name": "FAKÜLTE ACİL", "latitude": 38.70127, "longitude": 35.52053, "area": 3},
    {"intersection_id": 102, "intersection_name": "TALAS BULVARI LOJMAN GIRISI", "latitude": 38.69964, "longitude": 35.5266, "area": 3},
    {"intersection_id": 103, "intersection_name": "ERKILET BLV. - HACI OSMAN CD. ( FLASLAR )", "latitude": 38.81048, "longitude": 35.44942, "area": 5},
    {"intersection_id": 104, "intersection_name": "TALAS BAHÇELİEVLER GİRİŞ", "latitude": 38.69395, "longitude": 35.54593, "area": 3},
    {"intersection_id": 106, "intersection_name": "TALAS KAYMAKAMLIK", "latitude": 38.69295, "longitude": 35.54948, "area": 3},
    {"intersection_id": 108, "intersection_name": "TALAS DOMİNOS", "latitude": 38.6979, "longitude": 35.56014, "area": 3},
    {"intersection_id": 109, "intersection_name": "BAGDAT CD. TURGUT REIS CD.", "latitude": 38.73836, "longitude": 35.46088, "area": 5},
    {"intersection_id": 110, "intersection_name": "EŞREF BİTLİS", "latitude": 38.72516, "longitude": 35.52004, "area": 3},
    {"intersection_id": 113, "intersection_name": "TALAS BULVARI ( KIZILAY KAN MERKEZI) YAYA", "latitude": 38.69699, "longitude": 35.53516, "area": 3},
    {"intersection_id": 116, "intersection_name": "FURKAN DOĞAN", "latitude": 38.72156, "longitude": 35.52787, "area": 3},
    {"intersection_id": 119, "intersection_name": "KAYSERİ GAZ", "latitude": 38.74597, "longitude": 35.4883, "area": 5},
    {"intersection_id": 120, "intersection_name": "REKTÖRLÜK KAVŞAĞI", "latitude": 38.7114, "longitude": 35.53192, "area": 3},
    {"intersection_id": 123, "intersection_name": "HUZUREVİ KAVŞAĞI", "latitude": 38.76867, "longitude": 35.46223, "area": 5},
    {"intersection_id": 124, "intersection_name": "HALEF HOCA", "latitude": 38.70846, "longitude": 35.55502, "area": 3},
    {"intersection_id": 126, "intersection_name": "TALAS KIZ YURDU", "latitude": 38.69614, "longitude": 35.53823, "area": 3},
    {"intersection_id": 138, "intersection_name": "KOMANDO CAD", "latitude": 38.70046, "longitude": 35.52322, "area": 3},
    {"intersection_id": 139, "intersection_name": "YESIL MAH KÖPRÜ", "latitude": 38.75013, "longitude": 35.47102, "area": 5},
    {"intersection_id": 140, "intersection_name": "HOCA AHMET YESEVI CD. METEHAN SK. ( TALAS JANDARMA )", "latitude": 38.69668, "longitude": 35.55597, "area": 3},
    {"intersection_id": 142, "intersection_name": "TALAS CEMİL BABA", "latitude": 38.68926, "longitude": 35.55385, "area": 3},
    {"intersection_id": 147, "intersection_name": "KADİR HAS", "latitude": 38.75116, "longitude": 35.49129, "area": 5},
    {"intersection_id": 150, "intersection_name": "ERENKÖY KAVŞAĞI", "latitude": 38.6951, "longitude": 35.52923, "area": 3},
    {"intersection_id": 151, "intersection_name": "SAYER", "latitude": 38.69886, "longitude": 35.5658, "area": 3},
    {"intersection_id": 157, "intersection_name": "MURAT CD. - SUSURLUK SOKAK ( ITFAIYE ) FLAS", "latitude": 38.73695, "longitude": 35.50945, "area": 5},
    {"intersection_id": 160, "intersection_name": "KOMANDO CADDESI - ERCIYES KOLEJI BUTONLU YAYA", "latitude": 38.68403, "longitude": 35.54395, "area": 3},
    {"intersection_id": 161, "intersection_name": "ÇOCUK HASTANESİ", "latitude": 38.78122, "longitude": 35.45696, "area": 5},
    {"intersection_id": 162, "intersection_name": "KIZILIRMAK CADDESI - OLGUNLAR CD. ( ATLAS KOLEJI)", "latitude": 38.73083, "longitude": 35.52811, "area": 3},
    {"intersection_id": 163, "intersection_name": "BEKIR YILDIZ BLV. -  IHLAMUR CD. ( YENI PERVANE CAMI BUTONLU YAYA)", "latitude": 38.74655, "longitude": 35.50844, "area": 5},
    {"intersection_id": 166, "intersection_name": "FAKÜLTE IÇI YENI VETERINERLIK", "latitude": 38.70456, "longitude": 35.53926, "area": 3},
    {"intersection_id": 169, "intersection_name": "BARIS MANÇO CAD. - 14. CD. ( MEVLANA)", "latitude": 38.73847, "longitude": 35.48802, "area": 5},
    {"intersection_id": 170, "intersection_name": "MEHMET AKIF ERSOY CD. - YAVUZ SULTAN SELIM CD.", "latitude": 38.70034, "longitude": 35.55316, "area": 3},
    {"intersection_id": 171, "intersection_name": "MUSTAFA KEMAL PASA BLV. - KARDES SEHITLER CD. ( HAVALIMANI)", "latitude": 38.75843, "longitude": 35.48267, "area": 5},
    {"intersection_id": 174, "intersection_name": "Talas Servis Yolu", "latitude": 38.70043, "longitude": 35.52131, "area": 3},
    {"intersection_id": 175, "intersection_name": "KERTMELER", "latitude": 38.71996, "longitude": 35.5494, "area": 3},
    {"intersection_id": 180, "intersection_name": "ASIK VEYSEL BLV. - TEKNOPARK BUTONLU YAYA", "latitude": 38.7135, "longitude": 35.53131, "area": 3},
    {"intersection_id": 182, "intersection_name": "FAKÜLTE İÇİ HASTANELER", "latitude": 38.70459, "longitude": 35.52935, "area": 3},
    {"intersection_id": 183, "intersection_name": "SİVAS BLV. 384.SOKAK (KOCASİNAN MAH.) (BUTONLU )", "latitude": 38.770226, "longitude": 35.568147, "area": 5},
    {"intersection_id": 195, "intersection_name": "PARAŞÜT İNDİRME", "latitude": 38.68526, "longitude": 35.54235, "area": 3},
    {"intersection_id": 198, "intersection_name": "TALAS TOKİ", "latitude": 38.70311, "longitude": 35.55082, "area": 3},
    {"intersection_id": 204, "intersection_name": "BAYBURTLUOĞLU", "latitude": 38.70426, "longitude": 35.55672, "area": 3},
    {"intersection_id": 209, "intersection_name": "DADALOĞLU", "latitude": 38.79271, "longitude": 35.45184, "area": 5},
    {"intersection_id": 213, "intersection_name": "ORG.HULUSI AKAR BLV. MIGROS YAYA BUTONLU", "latitude": 38.7213, "longitude": 35.53619, "area": 3},
    {"intersection_id": 215, "intersection_name": "KOCASİNAN", "latitude": 38.77016, "longitude": 35.56806, "area": 5},
    {"intersection_id": 217, "intersection_name": "MUSTAFA KEMAL PASA BLV. - YAYA BUTONLU ( SEYRANI CAMI )", "latitude": 38.75496, "longitude": 35.48333, "area": 5},
    {"intersection_id": 224, "intersection_name": "UMUT CAD.", "latitude": 38.71942, "longitude": 35.55506, "area": 3},
    {"intersection_id": 229, "intersection_name": "BEKIR YILDIZ BLV.-ALINTERI CD", "latitude": 38.76258, "longitude": 35.43137, "area": 5},
    {"intersection_id": 232, "intersection_name": "İNCİLİ SOKAK KAV.", "latitude": 38.6862, "longitude": 35.54109, "area": 3},
    {"intersection_id": 233, "intersection_name": "MUSTAFA KEMAL PASA BLV. -  3.CD ( YAYA BUTONLU )", "latitude": 38.74249, "longitude": 35.48983, "area": 5},
    {"intersection_id": 234, "intersection_name": "ORG.HULUSI AKAR BLV. - TALAS ITFAIYE FLAS", "latitude": 38.71879, "longitude": 35.56388, "area": 3},
    {"intersection_id": 235, "intersection_name": "MİTHAT PAŞA YAYA", "latitude": 38.75325, "longitude": 35.46927, "area": 5},
    {"intersection_id": 237, "intersection_name": "BEKIR YILDIZ BLV  YAYA GEÇIS KAVSAGI", "latitude": 38.74957, "longitude": 35.46407, "area": 5},
    {"intersection_id": 239, "intersection_name": "BÜYÜKKILIÇ KAVŞAĞI", "latitude": 38.69017, "longitude": 35.53569, "area": 3},
    {"intersection_id": 243, "intersection_name": "HULISI AKAR BLV.1.YAYA BUTONLU", "latitude": 38.72163, "longitude": 35.53302, "area": 3},
    {"intersection_id": 244, "intersection_name": "HULISI AKAR BLV. 3.YAYA BUTONLU", "latitude": 38.7206, "longitude": 35.54288, "area": 3},
    {"intersection_id": 245, "intersection_name": "UMUT PAPATYA CAD.", "latitude": 38.7167, "longitude": 35.55578, "area": 3},
    {"intersection_id": 246, "intersection_name": "UMUT CAD. ISTASYON 5 YAYA", "latitude": 38.71407, "longitude": 35.55626, "area": 3},
    {"intersection_id": 247, "intersection_name": "UMUT CAD. 4. YAYA BUTONLU", "latitude": 38.71104, "longitude": 35.55656, "area": 3},
    {"intersection_id": 248, "intersection_name": "UMUT-TİMUÇİN", "latitude": 38.70845, "longitude": 35.55703, "area": 3},
    {"intersection_id": 249, "intersection_name": "M. TİMUÇİN ANAYURT", "latitude": 38.70851, "longitude": 35.5607, "area": 3},
    {"intersection_id": 250, "intersection_name": "MEHMET TIMUÇIN  ISTASYON 7 (ANAYURT PAZAR YERI) YAYA", "latitude": 38.70857, "longitude": 35.56237, "area": 3},
    {"intersection_id": 251, "intersection_name": "TURGUT-TİMUÇİN", "latitude": 38.70754, "longitude": 35.56582, "area": 3},
    {"intersection_id": 252, "intersection_name": "TURGUT ÖZAL CD. VILAYET SOKAK PALMIYE APT. BUTONLU YAYA GEÇITI 5", "latitude": 38.70553, "longitude": 35.56536, "area": 3},
    {"intersection_id": 253, "intersection_name": "TURGUT ÖZAL CD. CEMIL BABA CD.ISTASYON 9 GECELME", "latitude": 38.70181, "longitude": 35.56666, "area": 3},
    {"intersection_id": 262, "intersection_name": "ERKİLET KÜTÜPHANE", "latitude": 38.79034, "longitude": 35.45322, "area": 5},
    {"intersection_id": 265, "intersection_name": "BEKIR YILDIZ BLV.-ALINTERI CD", "latitude": 38.76258, "longitude": 35.43137, "area": 5},
    {"intersection_id": 267, "intersection_name": "Yesil Mah. Bulgurcu sok. Yaya", "latitude": 38.75712, "longitude": 35.46724, "area": 5},
    {"intersection_id": 268, "intersection_name": "15 TEMMUZ CD. KAYSERI ÜNIVERSITESI BUTONLU YAYA", "latitude": 38.71165, "longitude": 35.55209, "area": 3},
    {"intersection_id": 271, "intersection_name": "AKMESCIT-BEKIR YILDIZ BULV.", "latitude": 38.7497, "longitude": 35.49936, "area": 5},
    {"intersection_id": 273, "intersection_name": "SEYRANİ YAYA", "latitude": 38.7498, "longitude": 35.4832, "area": 5},
    {"intersection_id": 277, "intersection_name": "ERKİLET AKOĞLU CAD.", "latitude": 38.79761, "longitude": 35.44966, "area": 5},
    {"intersection_id": 280, "intersection_name": "Bağdat Cad. Yaya Butonlu", "latitude": 38.74232, "longitude": 35.45453, "area": 5},
    {"intersection_id": 500, "intersection_name": "Kerkük Bulvarı (OKUMA)", "latitude": 38.70241, "longitude": 35.53582, "area": 3},
    {"intersection_id": 508, "intersection_name": "Halef Hoca Cad. (OKUMA)", "latitude": 38.70213, "longitude": 35.55852, "area": 3},
    {"intersection_id": 524, "intersection_name": "Talas Bulvari-Çay Baglari Kesisimi", "latitude": 38.70067, "longitude": 35.52147, "area": 3},
    {"intersection_id": 525, "intersection_name": "TALAS HIZLI YOL (OKUMA)", "latitude": 38.70618, "longitude": 35.51016, "area": 3}
]

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
    # Flask uygulamasını başlatmadan önce tarayıcıyı aç
    url = "http://127.0.0.1:5000"
    print(f"Çalışıyor: {url} adresini tarayıcıda açabilirsiniz.")
    webbrowser.open(url)  # Tarayıcıyı açar
    app.run(debug=True)