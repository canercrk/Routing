# Rota Planlama Uygulaması

## 1. Arka Plan ve Genel Bakış

Bu proje, Kayseri Büyükşehir Belediyesi'nin operasyonel saha ekipleri (trafik kontrol, zabıta, atık yönetimi vb.) için geliştirilmiş bir rota optimizasyon ve karar destek sistemi sunar.

**İş Problemi:** Mevcut durumda, saha ekiplerinin güzergâh planlaması büyük ölçüde manuel süreçlere, sürücü tecrübesine ve subjektif değerlendirmelere dayanmaktadır. Bu yaklaşım; artan yakıt maliyetleri, gereksiz zaman kayıpları ve operasyonel verimsizliklere yol açmaktadır ve sabit trafik kontrol noktaları gibi zorunlu kısıtların denkleme dahil edilmesi, manuel planlamayı daha da karmaşık hale getirmektedir.

**İş Hedefi:** Projenin temel hedefi, manuel planlamayı otomatize ederek operasyonel maliyetleri düşürmek, zaman tasarrufu sağlamak ve saha ekiplerinin verimliliğini maksimize etmektir. Sistem, Kayseri yol ağını ve sabit kontrol noktalarını dikkate alarak, kullanıcı tarafından belirlenen noktalar arasında en en kısa rotayı saniyeler içinde hesaplayarak ölçülebilirliği, görünürlüğü sağlayarak görev tamamlama sürelerini iyileştirmek ve kaynak tahsisini optimize etmek hedeflenmektedir.

## 2. Veri Yapısı ve Modeli

Sistem, üç ana veri kaynağı ve bir grafik veri modeli üzerine kuruludur:

- **Yol Ağı Verisi (Graf):** Kayseri ilinin tamamına ait yol ağı, OpenStreetMap (OSM) üzerinden temin edilen veri, bir graf yapısına dönüştürülmüştür.
	- **Düğümler (Nodes):** Kavşakları ve yol kesişimlerini temsil eder.
	- **Kenarlar (Edges):** İki düğüm arasındaki yol segmentlerini temsil eder ve her kenar, 'mesafe' (metre) gibi ağırlıklandırma öz niteliklerine sahiptir.

- **Operasyonel Kısıt Verisi:** Kayseri Büyükşehir Belediyesi'nden temin edilen, 98 trafik kontrol noktasının ve stratejik kavşağın coğrafi (Enlem/Boylam) koordinatları rota hesaplamasında zorunlu veya ağırlıklandırılmış düğümler olarak görev yapar.
<img width="1123" height="737" alt="Image" src="https://github.com/user-attachments/assets/72374343-7c86-4cb4-903b-179830ec3447" />

- **Kullanıcı Girdi Verisi:** Uygulama arayüzünden kullanıcı tarafından sağlanan başlangıç noktası, bitiş noktası ve opsiyonel ara durakların koordinatları.

**Kavramsal Veri Modeli:** Sistemin çekirdeği, NetworkX kütüphanesi ile yönetilen ağırlıklı bir graf yapısıdır ve rota optimizasyonu, bu graf üzerinde en kısa yolu bulma problemi olarak matematiksel olarak modellenmiştir.

## 3. Yönetici Özeti

Bu analitik sistemin sağladığı temel iş değeri ve en önemli bulgular şunlardır:

- **Otomasyonun Getirisi:** Manuel ve hataya açık rota planlama süreci, yerini saniyeler içinde sonuç üreten otomatik bir sisteme bırakara planlama için harcanan idari zamanı ortadan kaldırmakta ve insan hatası riskini azaltmaktadır.

- **Maliyet Odaklı Planlama:** Sistem, sadece 'en kısa' mesafeyi değil, aynı zamanda 'en düşük maliyetli' rotayı da kullanıcının girdiği (L/100km ve Yakıt Fiyatı) parametrelerine göre dinamik olarak Yakıt Maliyeti (TL) ile beraber hesaplar, yöneticilere doğrudan parasal tasarruf odaklı kararlar alma imkânı sunar.

- **Operasyonel Uyum:** Rotalar, sahadaki gerçek bir zorunluluk olan "trafik kontrol noktalarını" kısıtlı geçiş düğümleri olarak dikkate alarak üretilen rotaların teorik değil, pratikte uygulanabilir ve operasyonel gereksinimlerle tam uyumlu olmasını sağlar.

- **Kullanıcı Erişilebilirliği:** Geliştirilen web arayüzü, teknik bilgisi olmayan saha amirlerinin veya operatörlerin dahi karmaşık, çok duraklı rotaları kolayca oluşturmasına, görsel olarak analiz etmesine ve .kml formatında dışa aktarmasına olanak tanır.
<img width="1920" height="927" alt="Image" src="https://github.com/user-attachments/assets/aedf3b5f-f239-4a88-9fa4-8ced8530e823" />
<img width="1920" height="928" alt="Image" src="https://github.com/user-attachments/assets/984ae344-c32f-4dcd-bb85-397d0d67a9a9" />

## 4. Derinlemesine Bakış

### Geçmiş Durum

Daha önce, bir saha ekibinin bir günlük planı, ekip liderinin tecrübesine dayalı olarak yaklaşık 15–20 dakikalık bir manuel planlama gerektiriyordu ve bu planlama genellikle "en bilindik" rotaları temel alıyor, ancak "en kısa" veya "en az maliyetli" rotayı garanti edemiyordu ayrıca yakıt ve zaman harcamaları, günden güne %15–20 oranında sapma gösterebiliyor ve ölçümlenmesi zordu.

### Analitik Modelin Çözümü

Geliştirilen sistem, bu süreci kökten değiştirmiştir artık aynı duraklı plan, kullanıcı tarafından arayüze girildiğinde 2–3 saniye içinde hesaplanmaktadır.

### İyileştirilen Temel İş Metrikleri

- Planlama Süresi (Time-to-Plan): 15–20 dakikalık manuel efordan, 2–3 saniyelik otomatik hesaplamaya düşürülerek operasyonel planlama verimliliğinde %99'un üzerinde bir iyileşme anlamı bizlere sunmaktadır.

- Operasyonel Maliyet (Cost-per-Task): Sistem, her rota için artık ölçülebilir maliyet metrikleri üretirerek bütçeleme ve kaynak tahsisinde doğrudan kullanılabilir bir veri görebiliriz.

- Rota Verimliliği (Distance-per-Stop): Model, "en bilindik" yol yerine "matematiksel olarak en kısa" yolu bularak, durak başına düşen mesafeyi optimize eder ve gereksiz kilometre kullanımını engeller.

## 5. Varsayımlar ve Çekinceler

Analiz süresince, modelin işleyişi için belirli varsayımlar yapılmış ve bu varsayımlardan doğan bazı çekinceler mevcuttur ve paydaşların bu noktaları dikkate alması gerekmektedir:

- Varsayım 1 (Statik Hız ve Trafik): Modelde anlık veya tarihsel trafik yoğunluğu verisi kullanılmaması nedenle, hesaplanan "tahmini süre" metriği, gerçek trafik durumunu yansıtmaz ve süre hesaplaması, tüm yol segmentleri için (eğer hız bilgisi eksikse) varsayılan 50 km/s hız kabulüne dayanarak "en kısa mesafe" üzerinden yapılır; "en hızlı" rota garanti edilmez.

- Varsayım 2 (Yol Ağı Güncelliği): Model, OpenStreetMap (OSM) veritabanının %100 doğru ve güncel olduğunu varsayarak sahadaki anlık yol kapanmalarını, plansız inşaat çalışmalarını, kazaları veya OSM'de henüz güncellenmemiş yeni açılan yolları hesaba katmaz.

- Varsayım 3 (Maliyet Girdisi): "Yakıt Maliyeti" (TL) ve "Yakıt Tüketimi" (L/100km) tamamen kullanıcı tarafından sağlanan girdilere dayanarak değerlerin doğruluğunu veya gerçekçiliğini doğrulamaz yani sonuç maliyet metriklerinin doğruluğu, doğrudan kullanıcının sağladığı verinin kalitesine bağlıdır.

## 6. Teknik Detaylar ve Kurulum

Projenin teknik altyapısı, kullanılan kütüphaneler ve kurulum detayları için lütfen aşağıdaki belgelere başvurunuz.

Haritalama, yerel yol ağından (OpenStreetMap) rota hesaplayıp görselleştirmek için geliştirilmiş, kullanıcı dostu bir Flask + OSMnx + Folium uygulamasıdır. Bu repo hem demo amaçlı interaktif harita sayfası (`htmls/`) hem de rota hesaplama backend'ini (`haritalamaGERL.py`) içerir.

Bu README üç hedefli: projeyi kısaca tanıtmak, hızlıca çalıştırmayı göstermek ve Netlify üzerinde yalnızca statik frontend yayınlamak isteyenler için yönlendirme sağlamaktır.

### Hızlı Başlangıç (lokal, geliştirme)

1) Depoyu klonlayın veya indirin (veya GitHub üzerinden dosyaları indirin).

2) **NOT:** Bu proje için sanal ortam (venv) oluşturmayın — doğrudan dosyaları indirip çalıştırmanız yeterlidir.

3) Gerekli paketleri yükleyin:

```bash
pip install -r requirements.txt
```

4) Uygulamayı başlatın:

```bash
python haritalamaGERL.py
```

Uygulama varsayılan olarak http://127.0.0.1:5000 adresinde çalışacaktır.
