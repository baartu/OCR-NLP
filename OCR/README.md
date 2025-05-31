# OCR ve NLP Analiz Sistemi

Bu proje, görsellerden metin çıkarma (OCR) ve doğal dil işleme (NLP) kullanarak metin analizi yapan bir web uygulamasıdır. Özellikle menü ve sokak tabelalarından metin çıkarma ve analiz etme konusunda uzmanlaşmıştır.

## Özellikler

- Görsel yükleme (sürükle-bırak desteği)
- İki farklı OCR motoru (Tesseract ve EasyOCR)
- Otomatik dil algılama (Türkçe ve İngilizce)
- Metin analizi:
  - Duygu analizi
  - Varlık tanıma
  - Anahtar kelime çıkarma
- Modern ve kullanıcı dostu arayüz
- Gerçek zamanlı sonuçlar

## Kurulum

1. Python 3.8 veya üstü sürümü yükleyin.

2. Tesseract OCR'ı yükleyin:
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`

3. Proje bağımlılıklarını yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

4. spaCy modelini yükleyin:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Kullanım

1. Uygulamayı başlatın:
   ```bash
   python app.py
   ```

2. Tarayıcınızda `http://localhost:5000` adresine gidin.

3. Bir görsel yükleyin (sürükle-bırak veya tıklayarak).

4. Sonuçları görüntüleyin:
   - Çıkarılan metin
   - Duygu analizi
   - Tanınan varlıklar
   - Anahtar kelimeler

## Gereksinimler

- Python 3.8+
- Tesseract OCR
- Flask
- OpenCV
- EasyOCR
- spaCy
- NumPy
- Pillow

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 