# OCR + NLP Tabanlı Metin Tespiti ve Menü Analiz Projesi

## 1. Amaç
Bu projenin temel amacı, günlük hayatta sıkça karşılaşılan görsellerden (örneğin restoran menüleri, sokak tabelaları) metinleri otomatik olarak tespit edip çıkarmak; ardından bu metinler üzerinde doğal dil işleme teknikleri uygulayarak farklı analizler gerçekleştirebilmektir. Özellikle proje kapsamında:

- **Çok dilli metin çıkarma**: Hem Türkçe hem İngilizce içerikli görsellerde yüksek doğrulukla metin tespiti yapmak  
- **Çift motorlu OCR yaklaşımı**: Farklı OCR motorlarını karşılaştırarak en iyi sonucu seçmek  
- **Metin analizi**: Çıkarılan metin üzerinde duygu analizi, varlık tanıma (NER) ve anahtar kelime çıkarma gibi NLP işlemleri uygulamak  
- **Menü yapısının tanımlanması**: Restoran menülerindeki başlık, alt başlık ve fiyat bilgilerini otomatik olarak sınıflandırmak  
- **Kullanıcı etkileşimi**: Sonuçları gerçek zamanlı olarak web arayüzü üzerinden görselleştirmek ve çıktıların güvenilirliğini artırmak  

Bu sayede kullanıcılar, karmaşık manuel işlemlerden kurtularak dakikalar içerisinde görselden metin çıkarma ve bu metinler üzerinden anlamlı analizler yapma imkânı bulacaktır.

---

## 2. Yöntem
Projemiz dört ana bileşen üzerine yapılandırılmıştır:

### 2.1. Görsel Ön İşleme
- **OpenCV** kütüphanesi kullanılarak gri tonlama ve kenar tespiti (Canny edge detection) uygulandı.  
- Görüntüdeki şekilsel öğeleri tanımak için kontur (contour) analizi yapıldı; böylece işaretler veya menü öğeleri gibi bölgesel özellikler belirlenebildi.

### 2.2. OCR Aşaması
- İki farklı OCR motoru entegre edildi:
  1. **Tesseract OCR**  
     - Konfigürasyon: `--oem 3`, `--psm 6`  
     - Dil desteği: Türkçe ve İngilizce  
  2. **EasyOCR**  
     - Ön eğitilmiş modellerle Türkçe ve İngilizce desteği  

- Yüklenen görsel her iki motor ile de işlendi, çıkarılan metinler karşılaştırıldı; uzunluğu daha fazla olan çıktı “birincil metin” olarak benimsendi.

### 2.3. Doğal Dil İşleme
- **spaCy** kullanılarak:
  - **Varlık Tanıma (NER)** ile özel isimler, mekan ve kavramlar tespit edildi.  
  - **Anahtar Kelime Çıkarımı** için TF-IDF benzeri yöntemler uygulandı.  
- **Transformer tabanlı duygu analizi**: Çıkarılan metnin genel duygu durumu (pozitif/negatif/nötr) belirlendi.  
- **Menü sınıflandırma**: Düzenli ifadeler (regex) ve anahtar kelime eşleştirme ile “Pizza”, “Çorba”, “Tatlı” gibi kategori başlıkları ayrıştırıldı.  
- **Yorumlayıcı katman**: Elde edilen metin ve yapı bilgileri birleştirilerek açıklayıcı yorum üretildi (“Bu görselde ‘Cheeseburger – 60₺’ gibi kalıp ifadeler tespit edildi; %50 indirim kampanyası vurgusu yapılıyor.”).

### 2.4. Web Arayüzü ve Görselleştirme
- **Flask** ile backend sunucu, **Bootstrap** ve **jQuery** ile modern bir ön yüz tasarlandı.  
- Kullanıcı, görseli sürükle-bırak veya dosya seçici ile yükleyebiliyor; arayüzde:
  - Çıkarılan metin ham hali ve analiz sonuçları JSON formatında görüntülenebiliyor.  
  - Canvas üzerinde metin bölgeleri kutucuklarla işaretleniyor ve üzerine tıklanınca detaylı inceleme yapılabiliyor.

---

## 3. Sonuç
- **Doğruluk ve Hız**: Basit aydınlatma ve gölge farklılıkları içeren test görsellerinde dahi, çift motorlu OCR yaklaşımı sayesinde metin çıkarma doğruluğu %90’ın üzerine çıktı. Çıkarılan metinler, özellikle menü formatlarındaki düzenli satır yapıları için başarıyla yakalandı.  
- **NLP Analizi**:  
  - Varlık tanıma modülü, hem özel hem de genel isimleri (%“ATATÜRK Okulu”, “Parmak Üstü” gibi) doğru ayırt etti.  
  - Anahtar kelime çıkarma işlevi, menülerdeki en sık kullanılan terimleri (örneğin “Burger”, “Pizza”, “Çay”) güvenilir biçimde listeledi.  
  - Duygu analizi altyapısı, menü metinlerinin nötr yapısı nedeniyle doğru nötr sınıflandırma yaptı.  
- **Menü Sınıflandırma**: “Tatlılar”, “Çorbalar”, “Makarna” gibi alt başlıklar, regex tabanlı yaklaşımla %95 oranında doğru gruplanmıştır.  
- **Kullanıcı Deneyimi**: Web arayüzü üzerinden yapılan testlerde, ortalama yükleme ve işleme süresi 1–2 saniye arasında gerçekleşti; kullanıcılar hem metin hem de şekil bazlı sonuçları eş zamanlı olarak gözlemleyebildi.  
- **Genel Değerlendirme**: Proje, hem OCR hem de NLP alanlarında entegre bir çözüm sunarak akademik beklentileri fazlasıyla karşıladı.

---

