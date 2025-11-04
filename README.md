# Kayseri Rota Planlama Uygulaması

## 1. Arka Plan ve Genel Bakış

Bu proje, Kayseri Büyükşehir Belediyesi'nin operasyonel saha ekipleri (trafik kontrol, zabıta, atık yönetimi vb.) için geliştirilmiş bir rota optimizasyon ve karar destek sistemi sunar.

**İş Problemi:** Mevcut durumda, saha ekiplerinin güzergâh planlaması büyük ölçüde manuel süreçlere, sürücü tecrübesine ve subjektif değerlendirmelere dayanmaktadır. Bu yaklaşım; artan yakıt maliyetleri, gereksiz zaman kayıpları ve operasyonel verimsizliklere yol açmaktadır. Sabit trafik kontrol noktaları gibi zorunlu kısıtların denkleme dahil edilmesi, manuel planlamayı daha da karmaşık hale getirmektedir.

**İş Hedefi:** Projenin temel hedefi, manuel planlamayı otomatize ederek operasyonel maliyetleri düşürmek, zaman tasarrufu sağlamak ve saha ekiplerinin verimliliğini maksimize etmektir. Sistem, Kayseri yol ağını ve sabit kontrol noktalarını dikkate alarak, kullanıcı tarafından belirlenen noktalar arasında en en kısa rotayı saniyeler içinde hesaplar. Bu sayede ölçülebilirliği, görünürlüğü sağlayarak görev tamamlama sürelerini iyileştirmek ve kaynak tahsisini optimize etmek hedeflenmektedir.

## 2. Veri Yapısı ve Modeli

Sistem, üç ana veri kaynağı ve bir grafik veri modeli üzerine kuruludur:

- **Yol Ağı Verisi (Graf):** Kayseri ilinin tamamına ait yol ağı, OpenStreetMap (OSM) üzerinden temin edilmiştir. Bu veri, bir graf yapısına dönüştürülmüştür.
	- **Düğümler (Nodes):** Kavşakları ve yol kesişimlerini temsil eder.
	- **Kenarlar (Edges):** İki düğüm arasındaki yol segmentlerini temsil eder. Her kenar, 'mesafe' (metre) gibi ağırlıklandırma öz niteliklerine sahiptir.

- **Operasyonel Kısıt Verisi:** Kayseri Büyükşehir Belediyesi'nden temin edilen, 98 trafik kontrol noktasının ve stratejik kavşağın coğrafi (Enlem/Boylam) koordinatları. Bu noktalar, rota hesaplamasında zorunlu veya ağırlıklandırılmış düğümler olarak görev yapar.
<img width="1123" height="737" alt="Image" src="https://github.com/user-attachments/assets/72374343-7c86-4cb4-903b-179830ec3447" />

- **Kullanıcı Girdi Verisi:** Uygulama arayüzünden kullanıcı tarafından sağlanan başlangıç noktası, bitiş noktası ve opsiyonel ara durakların koordinatları.

**Kavramsal Veri Modeli:** Sistemin çekirdeği, NetworkX kütüphanesi ile yönetilen ağırlıklı bir graf yapısıdır. Rota optimizasyonu, bu graf üzerinde en kısa yolu bulma problemi olarak matematiksel olarak modellenmiştir.

## 3. Yönetici Özeti

Bu analitik sistemin sağladığı temel iş değeri ve en önemli bulgular şunlardır:

- **Otomasyonun Getirisi:** Manuel ve hataya açık rota planlama süreci, yerini saniyeler içinde sonuç üreten otomatik bir sisteme bırakmıştır. Bu, planlama için harcanan idari zamanı ortadan kaldırmakta ve insan hatası riskini azaltmaktadır.

- **Maliyet Odaklı Planlama:** Sistem, sadece 'en kısa' mesafeyi değil, aynı zamanda 'en düşük maliyetli' rotayı da hesaplamaktadır. Kullanıcının girdiği (L/100km ve Yakıt Fiyatı) parametrelerine göre dinamik olarak hesaplanan Yakıt Maliyeti (TL), yöneticilere doğrudan parasal tasarruf odaklı kararlar alma imkânı sunar.

- **Operasyonel Uyum:** Rotalar, sahadaki gerçek bir zorunluluk olan "trafik kontrol noktalarını" kısıtlı geçiş düğümleri olarak dikkate alır. Bu, üretilen rotaların teorik değil, pratikte uygulanabilir ve operasyonel gereksinimlerle tam uyumlu olmasını sağlar.

- **Kullanıcı Erişilebilirliği:** Geliştirilen web arayüzü, teknik bilgisi olmayan saha amirlerinin veya operatörlerin dahi karmaşık, çok duraklı rotaları kolayca oluşturmasına, görsel olarak analiz etmesine ve .kml formatında dışa aktarmasına olanak tanır.
<img width="1920" height="928" alt="Image" src="https://github.com/user-attachments/assets/8d7d6a04-0613-4c3c-81c7-c810c59c1f51" />
<img width="1920" height="928" alt="Image" src="https://github.com/user-attachments/assets/984ae344-c32f-4dcd-bb85-397d0d67a9a9" />

## 4. Derinlemesine Bakış

### Geçmiş Durum (Tarihsel Trend)

Daha önce, bir saha ekibinin bir günlük planı, ekip liderinin tecrübesine dayalı olarak yaklaşık 15–20 dakikalık bir manuel planlama gerektiriyordu. Bu planlama genellikle "en bilindik" rotaları temel alıyor, ancak "en kısa" veya "en az maliyetli" rotayı garanti edemiyordu. Yakıt ve zaman harcamaları, günden güne %15–20 oranında sapma gösterebiliyor ve ölçümlenmesi zordu.

### Analitik Modelin Çözümü (Yeni Durum)

Geliştirilen sistem, bu süreci kökten değiştirmiştir. Artık aynı duraklı plan, kullanıcı tarafından arayüze girildiğinde 2–3 saniye içinde hesaplanmaktadır.

### İyileştirilen Temel İş Metrikleri

- Planlama Süresi (Time-to-Plan): 15–20 dakikalık manuel efordan, 2–3 saniyelik otomatik hesaplamaya düşürülmüştür. Bu, operasyonel planlama verimliliğinde %99'un üzerinde bir iyileşme anlamına gelir.

- Operasyonel Maliyet (Cost-per-Task): Sistem, her rota için artık ölçülebilir maliyet metrikleri üretir. Bu, bütçeleme ve kaynak tahsisinde doğrudan kullanılabilir bir veridir.

- Rota Verimliliği (Distance-per-Stop): Model, "en bilindik" yol yerine "matematiksel olarak en kısa" yolu bularak, durak başına düşen mesafeyi optimize eder ve gereksiz kilometre kullanımını engeller.

- Şekil 1: Sistemin ana arayüzü ve harita üzerinde gösterilen operasyonel noktalar.

- Şekil 2: Başlangıç, bitiş ve ara duraklar seçildikten sonra hesaplanan optimize edilmiş rota ve yolculuk detayları (Mesafe, Süre, Maliyet).

## 5. Varsayımlar ve Çekinceler

Analiz süresince, modelin işleyişi için belirli varsayımlar yapılmış ve bu varsayımlardan doğan bazı çekinceler mevcuttur. Paydaşların bu noktaları dikkate alması gerekmektedir:

- Varsayım 1 (Statik Hız ve Trafik): Modelde anlık veya tarihsel trafik yoğunluğu verisi kullanılmamaktadır. Bu nedenle, hesaplanan "tahmini süre" metriği, gerçek trafik durumunu yansıtmaz. Süre hesaplaması, tüm yol segmentleri için (eğer hız bilgisi eksikse) varsayılan 50 km/s hız kabulüne dayanarak "en kısa mesafe" üzerinden yapılır; "en hızlı" rota garanti edilmez.

- Varsayım 2 (Yol Ağı Güncelliği): Model, OpenStreetMap (OSM) veritabanının %100 doğru ve güncel olduğunu varsayar. Analiz, sahadaki anlık yol kapanmalarını, plansız inşaat çalışmalarını, kazaları veya OSM'de henüz güncellenmemiş yeni açılan yolları hesaba katmaz.

- Varsayım 3 (Maliyet Girdisi): "Yakıt Maliyeti" (TL) ve "Yakıt Tüketimi" (L/100km) tamamen kullanıcı tarafından sağlanan girdilere dayanır. Model, bu değerlerin doğruluğunu veya gerçekçiliğini doğrulamaz. Sonuç maliyet metriklerinin doğruluğu, doğrudan kullanıcının sağladığı verinin kalitesine bağlıdır.

## 6. Teknik Detaylar ve Kurulum

Projenin teknik altyapısı, kullanılan kütüphaneler ve kurulum detayları için lütfen aşağıdaki belgelere başvurunuz.

Haritalama, yerel yol ağından (OpenStreetMap) rota hesaplayıp görselleştirmek için geliştirilmiş, kullanıcı dostu bir Flask + OSMnx + Folium uygulamasıdır. Bu repo hem demo amaçlı interaktif harita sayfası (`htmls/`) hem de rota hesaplama backend'ini (`haritalamaGERL.py`) içerir.

Bu README üç hedefli: projeyi kısaca tanıtmak, hızlıca çalıştırmayı göstermek ve Netlify üzerinde yalnızca statik frontend yayınlamak isteyenler için yönlendirme sağlamaktır.

### Hızlı Başlangıç (lokal, geliştirme)

1) Depoyu klonlayın veya indirin (veya GitHub üzerinden dosyaları indirin).

2) **NOT:** Bu proje için sanal ortam (venv) oluşturmayın — doğrudan dosyaları indirip çalıştırmanız yeterlidir.

3) Gerekli paketleri yükleyin (sadece bir kez):

```bash
pip install -r requirements.txt
```

4) Uygulamayı başlatın:

```bash
python haritalamaGERL.py
```

Uygulama varsayılan olarak http://127.0.0.1:5000 adresinde çalışacaktır.
