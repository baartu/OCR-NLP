import os
from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import pytesseract
import easyocr
import spacy
from PIL import Image
from werkzeug.utils import secure_filename
import difflib

# Windows için Tesseract yolunu ayarla
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Yeni Fonksiyon: Şekil Tabanlı Görüntü Tipi Tespiti
def detect_image_type_based_on_shape(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Uyarı: Görüntü yüklenemedi: {image_path}")
            return ""

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        img_h, img_w = img.shape[:2]
        img_area = img_h * img_w
        sign_like_contours_count = 0
        triangle_contours_count = 0  # Üçgen sayaç

        for contour in contours:
            contour_area = cv2.contourArea(contour)
            
            # Çok küçük veya çok büyük (neredeyse tüm görüntü) konturları atla
            if contour_area < 0.005 * img_area or contour_area > 0.9 * img_area:
                continue

            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True) # Köşe sayısını bulmak için poligon yaklaştır

            num_vertices = len(approx)
            
            # Üçgen kontrolü
            if num_vertices == 3:
                triangle_contours_count += 1
                continue
            # Tipik tabela şekilleri: dikdörtgen (4), altıgen (6), sekizgen (8)
            if 4 <= num_vertices <= 8:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                
                # Tabela benzeri oranlar (ne çok ince/uzun ne de çok geniş/kısa)
                if 0.2 < aspect_ratio < 5.0:
                    # Konturun görüntü merkezine yakınlığına da bakılabilir
                    # Şimdilik bu temel kontroller yeterli
                    sign_like_contours_count += 1
        
        # Öncelik üçgen ise onu döndür
        if triangle_contours_count > 0:
            return "Görselde üçgen şekilli bir tabela tespit edildi. "
        if sign_like_contours_count > 0: # En az bir adet potansiyel tabela şekli bulunduysa
            return "Görsel, şekil itibarıyla bir tabelaya veya benzeri bir nesneye benziyor. "
        return ""
    except Exception as e:
        print(f"Hata (detect_image_type_based_on_shape): {e}")
        return ""

# OCR ve NLP init
nlp = spacy.load("en_core_web_sm")
reader = None


menu_keywords = [
    # Küçük harfli anahtar kelimeler
    "menü", "sipariş", "fiyat listesi", "menu", "order", "restaurant",
    "cafe", "kafe", "bar", "lounge", "bistro", "pizzeria", "kebap",
    "restoran", "lokanta", "pastane", "fırın", "yemek", "içecek", "mutfak",
    "kahve türleri", "pizza çeşitleri", "çay çeşitleri", "makarna çeşitleri",
    "tatlılar", "çorbalar", "salatalar", "ızgaralar", "içecekler", "sıcaklar",
    # Menü kategorileri (eklenenler)
    "başlangıç", "ana yemek", "ara sıcak", "içecekler",
    # Büyük harfli versiyonlar
    "ÇORBALAR", "SALATALAR", "TATLILAR", "IZGARALAR", "İÇECEKLER", "SICAKLAR",
    "BAŞLANGIÇ", "ANA YEMEK", "ARA SICAK", "İÇECEKLER",
    # OCR varyasyonlarını yakalamak için boşluksuz versiyonlar
    "kahvetürleri", "pizzaçeşitleri", "çayçeşitleri", "makarnaçeşitleri",
    # OCR hataları için olası varyasyonlar
    "corbalar", "salatalar", "tatlilar", "icecekler", "izgaralar", "sicaklar"
]

def initialize_ocr():
    global reader
    if reader is None:
        reader = easyocr.Reader(['tr','en'], gpu=False)
    return reader

# Görsel ön işleme
def process_image(path):
    img = cv2.imread(path)
    if img is None:
        raise ValueError("Görüntü yüklenemedi")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    return cv2.dilate(thresh, kernel, iterations=1)

# OCR: EasyOCR + Bounding Box bilgisi
def extract_easyocr_with_bboxes(path):
    reader = initialize_ocr()
    img = cv2.imread(path)
    if img is None:
        raise ValueError("Görüntü yüklenemedi")
    results = reader.readtext(img)
    bboxes = []
    MIN_CONFIDENCE = 0.4 # Güven eşiği (0.0 ile 1.0 arası)
    for bbox_points, text, conf in results:
        if conf >= MIN_CONFIDENCE: # Sadece eşik değerinden yüksek güvene sahip metinleri al
            xs = [p[0] for p in bbox_points]
            ys = [p[1] for p in bbox_points]
            x, y = min(xs), min(ys)
            w, h = max(xs) - x, max(ys) - y
            bboxes.append({
                'text': text,
                'confidence': round(conf, 2),
                'bbox': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
            })
    # Sadece filtrelenmiş metinlerden tam metni oluştur
    full_text = ' '.join([b['text'] for b in bboxes])
    return full_text, bboxes

# OCR: Tesseract
def extract_text_tesseract(path):
    img = process_image(path)
    return pytesseract.image_to_string(img, lang='tur+eng')

# Menü kategorilendirme
def categorize_menu(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    menu = {}
    current = None
    for line in lines:
        if any(x in line.lower() for x in ['türleri', 'çeşitleri']):
            current = line
            menu[current] = []
            continue
        if current:
            parts = line.rsplit(' ', 1)
            if len(parts) == 2 and parts[1].replace('₺','').replace('tl','').isdigit():
                name, price = parts
                menu[current].append({'item': name, 'price': price})
            else:
                menu[current].append({'item': line})
    return menu

# Metin analizi: Entities + noun_chunks
def analyze_text(text):
    doc = nlp(text)
    return {
        'entities': [{'text': ent.text, 'label': ent.label_} for ent in doc.ents],
        'key_phrases': [chunk.text for chunk in doc.noun_chunks]
    }

# Görüntü içeriğini yorumlama (YENİ VERSİYON)
def interpret_image_content(text, menu_data, shape_hint_text):
    # Boş metin kontrolü
    if not text.strip():
        return "Bu görüntüde yazı bulunamadı."
        
    text_lower = text.lower()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    word_count = len(text.split())
    char_count = len(text.replace(" ", "").replace("\n", ""))

    print("OCR Çıktısı:", text)  # DEBUG: OCR çıktısını terminale yaz

    def fuzzy_contains(line, keywords, threshold=0.8):
        for kw in keywords:
            seq = difflib.SequenceMatcher(None, line.lower(), kw.lower())
            if seq.ratio() > threshold:
                return True
        return False

    # --- ÇOĞUNLUK MANTIĞI İLE MENÜ TESPİTİ ---
    menu_count = 0
    other_count = 0
    price_count = 0
    price_keywords = ["₺", "tl", ",00", ",50", ",25"]
    for line in lines:
        if fuzzy_contains(line, menu_keywords):
            menu_count += 1
        if any(pk in line.lower() for pk in price_keywords):
            price_count += 1
    menu_score = menu_count + price_count

    sign_keywords = [
        "danger", "warning", "caution", "hız sınırı", "speed limit", "yol yapımı", "road construction",
        "dikkat çalışma var", "road work", "dur", "stop", "exit", "giriş", "çıkış", "entrance", "way out",
        "park", "parking", "yasaktır", "no parking", "forbidden", "bilgi", "information", "danışma"
    ]
    for line in lines:
        if fuzzy_contains(line, sign_keywords):
            other_count += 1

    if menu_score > other_count:
        return "Bu bir menü, fiyat listesi veya yiyecek/içecek sunan bir işletmeyle ilgili olabilir. Genellikle seçenekleri ve fiyatları listeler ve sipariş vermek için kullanılır."


    if "danger" in text_lower or "warning" in text_lower or "caution" in text_lower:
        if "do not touch" in text_lower:
            return "Bu bir uyarı tabelasıdır ve 'Tehlikeli, dokunmayın' gibi bir ibare içermektedir. Bu, belirtilen nesneye dokunmanın ciddi tehlikelere yol açabileceği anlamına gelir, bu yüzden kesinlikle uzak durulmalıdır."
        return "Bu bir uyarı veya tehlike işaretidir. Bu, çevrenizde potansiyel bir risk olduğunu ve ekstra dikkatli olmanız gerektiğini gösterir."

    if "hız sınırı" in text_lower or "speed limit" in text_lower:
        import re
        match = re.search(r'(\d+)', text)
        if match:
            speed = match.group(1)
            return f"Bu bir hız sınırı tabelasıdır ve '{speed}' ibaresi bulunmaktadır. Bu, belirtilen hız limitini ({speed} km/s veya mil/s) aşmamanız gerektiği, aksi takdirde trafik kurallarını ihlal etmiş olacağınız ve güvenliğinizi riske atacağınız anlamına gelir."
        return "Bu bir hız sınırı tabelasıdır. Bu, belirtilen hız limitine uymanız gerektiği anlamına gelir, aksi takdirde trafik güvenliği tehlikeye girebilir."

    if "yol yapımı" in text_lower or "road construction" in text_lower or "dikkat çalışma var" in text_lower or "road work" in text_lower:
        return "Bu bir yol yapım çalışması tabelasıdır. Bu, ileride yolda çalışma olduğunu, trafiğin yavaşlayabileceğini, şerit daralmaları veya yönlendirmeler olabileceğini ve bu bölgede özellikle dikkatli ve yavaş ilerlemeniz gerektiğini gösterir. Olası gecikmeleri hesaba katmak iyi bir fikir olabilir."

    if ("dur" == text_lower.strip() or "stop" == text_lower.strip()) and len(text_lower.split()) < 3:
        return "Bu bir 'DUR' işaretidir. Bu, kavşağa veya kontrol noktasına yaklaşırken tamamen durmanız, yolu kontrol etmeniz ve güvenli olduğunda devam etmeniz gerektiği anlamına gelir."

    if "exit" in text_lower or "giriş" in text_lower or "çıkış" in text_lower or "entrance" in text_lower or "way out" in text_lower:
        return "Bu bir yönlendirme tabelasıdır (giriş, çıkış, bir yerin istikameti vb. bilgiler içeriyor olabilir). Bu, belirli bir yere nasıl ulaşılacağını veya bir alandan nasıl çıkılacağını gösterir."
        
    if "park" in text_lower or "parking" in text_lower:
        if "yasaktır" in text_lower or "no parking" in text_lower or "forbidden" in text_lower:
            return "Bu bir park yasağı tabelasıdır. Bu, aracınızı belirtilen alana park etmenin yasak olduğu ve muhtemelen cezai işlem uygulanabileceği anlamına gelir."
        return "Bu, park etme kuralları, izinleri veya olanakları hakkında bilgi veren bir tabeladır. Koşulları ve geçerlilik sürelerini dikkatlice okumanız önemlidir."

    if "bilgi" in text_lower or "information" in text_lower or "danışma" in text_lower:
        return "Bu genel bir bilgilendirme metni veya tabelasıdır. İçerdiği özel bilgiye göre hareket etmeniz veya dikkate almanız gerekebilir."

    # 3. SON OLARAK: Genel tabela kontrolü
    if shape_hint_text:
        # Eğer anlamlı bir metin yoksa sadece şekil ipucu döndür, ek açıklama verme
        if char_count < 3:
            return shape_hint_text.strip()
        if 1 <= len(lines) <= 4 and word_count <= 10:
            return shape_hint_text + "Bir işletme adı, logosu, kısa bir duyuru veya genel bir tabela olabilir."
        else:
            return shape_hint_text + "Genel bir metin içeren bir tabela olabilir."

    # 4. Varsayılan Durum
    return "Bu bir düz yazıdır."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(error='No file part'), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify(error='No selected file'), 400

    try:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        #  Şekil tabanlı
        shape_hint = detect_image_type_based_on_shape(path)

        # 1) EasyOCR metni + bbox
        txt_easy, bboxes = extract_easyocr_with_bboxes(path)
        # 2) Tesseract metni
        txt_tess = extract_text_tesseract(path)
        # 3) En uzun metni seç
        final_text = txt_easy if len(txt_easy) > len(txt_tess) else txt_tess

        analysis = analyze_text(final_text)
        menu_struct = categorize_menu(final_text)
        final_interpretation = interpret_image_content(final_text, menu_struct, shape_hint)

        # Geçici dosyayı sil
        os.remove(path)

        return jsonify({
            'text': final_text,
            'bboxes': bboxes,
            'analysis': analysis,
            'menu': menu_struct,
            'interpretation': final_interpretation
        })
    except Exception as e:
        # Hata durumunda geçici dosyayı temizle
        if 'path' in locals():
            try:
                os.remove(path)
            except:
                pass
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')