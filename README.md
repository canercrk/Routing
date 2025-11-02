# Kayseri Rota Planlama Uygulaması
# Haritalama — Akıllı Rota ve Görselleştirme

Haritalama, yerel yol ağından (OpenStreetMap) rota hesaplayıp görselleştirmek için geliştirilmiş, kullanıcı dostu bir Flask + OSMnx + Folium uygulamasıdır. Bu repo hem demo amaçlı interaktif harita sayfası (`htmls/`) hem de rota hesaplama backend'ini (`haritalamaGERL.py`) içerir.

Bu README üç hedefli: projeyi kısaca tanıtmak, hızlıca çalıştırmayı göstermek ve Netlify üzerinde yalnızca statik frontend yayınlamak isteyenler için yönlendirme sağlamaktır.

Hızlı Başlangıç (lokal, geliştirme)
1) Depoyu klonlayın veya indirin (veya GitHub üzerinden dosyaları indirin).

2) NOT: Bu proje için sanal ortam (venv) oluşturmayın — doğrudan dosyaları indirip çalıştırmanız yeterlidir.

3) Gerekli paketleri yükleyin (sadece bir kez):

```bash
pip install -r requirements.txt
```

4) Uygulamayı başlatın:

```bash
python haritalamaGERL.py
```
Uygulama varsayılan olarak http://127.0.0.1:5000 adresinde çalışacaktır.

Notlar
- OSMnx, ilk ağ indirme sırasında büyük veri çekebilir ve biraz zaman alabilir. `get_cached_graph` fonksiyonu grafı önbelleğe alır.

## 1. Genel Amaç
Bu yazılım, Kayseri şehri için bir rota planlama ve analiz uygulamasıdır. Kullanıcılar harita üzerinde bir başlangıç noktası, bir bitiş noktası ve isteğe bağlı ara duraklar seçebilir. Kod, bu noktalar arasında en kısa ve en uygun rotayı bulur, şunları hesaplar:
- Toplam mesafe
- Tahmini yolculuk süresi
- Yakıt tüketimi ve maliyeti
- Rotayı harita üzerinde görselleştirir
- Kullanıcıların rotayı KML dosyası olarak indirip başka harita uygulamalarında kullanmasına olanak tanır.

## 2. Uygulama Nasıl Çalışır?
1. **Kullanıcı Arayüzü:**
   - Kullanıcı bir web sayfası açar, başlangıç/bitiş/ara durakları seçer ve araç bilgilerini (yakıt tüketimi, fiyat) girer.
   - "Rotayı Hesapla" butonuna tıklar.
2. **Verilerin Sunucuya Gönderilmesi:**
   - Seçilen noktalar ve bilgiler sunucuya (bu kodun çalıştığı bilgisayara) gönderilir.
3. **Sunucu Tarafında İşlemler:**
   - **Harita Verisi Hazırlanır:** Kayseri'nin yol ağı belleğe yüklenir (önbellekten veya OSM'den).
   - **Noktalar Eşleştirilir:** Kullanıcı noktaları en yakın yollara eşlenir.
   - **Rota Hesaplanır:**
     - En kısa rota bulunur (Dijkstra algoritması ile).
     - Ara duraklar varsa, en uygun sıralama belirlenir.
   - **Mesafe, Süre ve Maliyet Hesaplanır:**
     - Her yol parçasının uzunluğu ve hızı ile toplam mesafe ve süre hesaplanır.
     - Yakıt tüketimi ve maliyeti, kullanıcının girdiği değerlere göre hesaplanır.
   - **Sonuçlar Hazırlanır:**
     - Rota haritada çizilir, duraklar işaretlenir ve tüm sonuçlar kullanıcıya sunulur.
4. **Sonuçların Gösterilmesi:**
   - Kullanıcı, harita üzerinde rotayı, mesafeyi, süreyi, yakıtı ve maliyeti görür.
   - İsterse rotayı KML dosyası olarak indirebilir.

## 3. Kullanılan Temel Algoritmalar ve Yöntemler
- **Dijkstra Algoritması:**
  - Harita üzerinde iki nokta arasındaki en kısa yolu bulur.
  - NetworkX kütüphanesinin `shortest_path` fonksiyonu ile kullanılır.
  Başlangıç düğümüne 0, diğerlerine sonsuz mesafe atanır.
  Henüz işlenmemiş düğümler arasından en kısa mesafeye sahip olan seçilir.
  Seçilen düğümün komşularının mesafeleri güncellenir.
  Tüm düğümler işlenene kadar adımlar tekrarlanır.
  weight='length': Kenarların fiziksel uzunluğunu (metre) dikkate alır.
  Örnek: A → B → C rotası, A → C'den daha uzunsa Dijkstra en kısayı (A → C) seçer.
- **Permütasyon & Greedy Algoritma:**
  - Az sayıda ara durak varsa, tüm olası sıralamalar denenir ve en kısa rota bulunur. 3

  - Çok ara durak varsa, hızlı bir şekilde yaklaşık çözüm için greedy (her adımda en yakın noktaya git) yöntemi kullanılır. 4+
  Ara durakların sıralamasını optimize eder (örn., A → B → C yerine A → C → B daha verimliyse).
  Projede `order = nearest_neighbor_order` fonksiyonunda kullanılır

  **Haversine Formülü**
    İki koordinat arasındaki kuş uçuşu mesafeyi hesaplar.
    Graf kenarlarında length bilgisi yoksa yedek olarak kullanılır.
    `dist_meters = great_circle((lat1, lon1), (lat2, lon2)).meters`
- **Yakıt ve Süre Hesaplama:**
  - Her yol parçasının uzunluğu ve hızı ile süre hesaplanır.
  - Hız verisi yoksa, Türkiye trafik yönetmeliğine göre varsayılan hızlar atanır.
  - Yakıt maliyeti, kullanıcıdan alınan verilere göre hesaplanır.

  **LineString Geometri İşleme**
    OpenStreetMap'ten alınan yol geometrilerini (LineString) birleştirerek rotayı oluşturur.

    Her graf kenarının geometry özelliği kontrol edilir.
    Geometri varsa koordinatlar çıkarılır, yoksa düğüm koordinatları kullanılır.

    Tüm koordinatlar birleştirilerek tek bir rota çizgisi oluşturulur.
    `route_geometry = get_route_geometry(G, full_route)`

## Algoritmaların Projedeki İş Bölümü
Algoritma 	Kullanım Amacı        	Kullanan Fonksiyon

Dijkstra  	Temel rota hesaplama  	nx.shortest_path
Greedy    	Ara durakları sıralama	nearest_neighbor_order
Haversine 	Kuş uçuşu mesafe      	great_circle
LineString	Rota geometrisi       	get_route_geometry

## Örnek Senaryo ile Çalışma Akışı
Kullanıcı girdileri alınır: Başlangıç (A), Bitiş (D), Ara Duraklar (B, C).

Dijkstra çalışır: A → B, B → C, C → D segmentleri ayrı ayrı hesaplanır.

Greedy sıralama yapar: B ve C'nin konumuna göre optimal sıra belirlenir (A → B → C → D).

Haversine devreye girer: Herhangi bir graf kenarında geometri yoksa mesafe hesaplanır.

Folium haritayı çizer: Tüm koordinatlar birleştirilerek kullanıcıya gösterilir.



## 4. Ana Fonksiyonlar ve Görevleri
- **SimpleCache:**
  - Harita verisini bellekte hızlı erişim için saklar.
- **get_cached_graph:**
  - Kayseri'nin yol ağını yükler (önbellekten veya OSM'den).
- **nearest_neighbor_order:**
  - Ara duraklar için en kısa toplam mesafeyi sağlayacak en iyi sıralamayı bulur.
- **get_route_geometry:**
  - Rotanın gerçek geometrisini (kıvrımlar dahil) çıkarır, harita ve KML için kullanılır.
- **create_map:**
  - Rotayı ve durakları kullanıcıya harita üzerinde çizer.
- **calculate_route:**
  - Ana fonksiyon: en kısa rotayı bulur, mesafe/süre/maliyet hesaplar ve haritayı hazırlar.
- **Flask Web Servisleri:**
  - `/` : Ana sayfa
  - `/calculate` : Rota hesaplama
  - `/get_intersections` : Kavşak/durak verisi
  - `/download_kml` : Rotayı KML dosyası olarak indirme

## 5. Temel Bileşenler
- **Harita Verisi:**
  - Kayseri'nin yolları, kavşakları ve bağlantıları bir ağ olarak tutulur.
- **Kullanıcı Noktaları:**
  - Kullanıcının seçtiği noktalar en yakın yollara eşlenir.
- **Rota Hesaplama:**
  - Bilgisayar, bu noktalar arasında en kısa ve mantıklı rotayı bulur.
- **Mesafe ve Süre:**
  - Her yol parçasının uzunluğu ve hızı ile toplam mesafe ve tahmini süre hesaplanır.
- **Yakıt ve Maliyet:**
  - Kullanıcının araç bilgisiyle toplam yakıt ve maliyet hesaplanır.
- **Harita Çizimi:**
  - Sonuçlar, harita üzerinde renkli çizgiler ve işaretlerle gösterilir.
- **KML Dosyası:**
  - Kullanıcı, rotayı başka harita uygulamalarında kullanmak için dosya olarak indirebilir.

## 6. Teknik Terimler ve Açıklamaları
- **Rota:** Başlangıçtan bitişe, varsa ara duraklara uğrayarak izlenen yol.
- **Düğüm (Node):** Harita üzerindeki bir kavşak, durak veya yol noktası.
- **Kenar (Edge):** İki düğüm arasındaki yol parçası.
- **KML:** Harita uygulamalarında rota göstermek için kullanılan bir dosya formatı.
- **Permütasyon:** Bir grup nesnenin (burada ara duraklar) tüm olası sıralamalarını denemek.
- **Greedy Algoritma:** Her adımda en iyi görünen seçimi yaparak hızlıca çözüm bulmaya çalışan yöntem.
- **Dijkstra Algoritması:** İki nokta arasındaki en kısa yolu bulan matematiksel yöntem.

## 7. Özet
Bu kod, harita üzerinde rota planlamak isteyen birinin:
- Başlangıç, bitiş ve ara durakları seçerek
- En kısa ve uygun rotayı bulmasını,
- Yolculuk süresi, mesafesi ve maliyetini öğrenmesini,
- Sonucu harita üzerinde görmesini,
- Ve isterse bu rotayı bilgisayarına kaydetmesini sağlar.

Her şey otomatik ve kullanıcı dostu şekilde gerçekleşir. Kullanıcıdan alınan bilgilerle, bilgisayar arka planda en iyi rotayı bulur ve gösterir.
