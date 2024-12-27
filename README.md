# Nyxie: Gelişmiş Telegram AI Chatbot 

## Proje Genel Bakış

Nyxie, Stixyie tarafından geliştirilen gelişmiş bir Protogen AI chatbot'udur. Telegram üzerinde çalışan bu bot, kullanıcılarıyla etkileşime giren, duyarlı ve çok yönlü bir yapay zeka asistanıdır.

## Özellikler

### 1. Çoklu Dil Desteği
- Otomatik dil algılama
- Kullanıcının dilinde yanıt verme yeteneği
- Esnek dil yönetimi

### 2. Gelişmiş Bellek Yönetimi
- Kullanıcı başına maksimum 1 milyon token
- Konuşma geçmişini dinamik olarak yönetme
- Her kullanıcı için ayrı bellek dosyaları

### 3. Çoklu Medya Desteği
- Metin mesajları
- Görüntü işleme
- Video analizi

### 4. Kişilik Özellikleri
- Empati kurabilen ve duyarlı bir AI
- Teknoloji ve yaşam hakkında derin bilgi
- Yaratıcı ve öğrenmeye açık kişilik

## Teknolojiler

- Python 3.8+
- Google Gemini AI
- Google Cloud Vision
- Telegram Bot API
- LangDetect
- Pillow (Görüntü İşleme)

## Gereksinimler

- Python 3.8 veya üzeri
- Telegram Bot Token
- Google Gemini API Key
- Google Cloud Vision API Key (isteğe bağlı)

## Kurulum

1. Depoyu klonlayın:
```bash
git clone https://github.com/Stixyie/Nyxie-Protogen-Chatbot-Telegram
cd Nyxie-Protogen-Chatbot-Telegram
```

2. Sanal ortam oluşturun:
```bash
python -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate
```

3. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

4. `.env` dosyasını yapılandırın:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

## Kullanım

Bot'u başlatmak için:
```bash
python bot.py
```

### Telegram Komutları
- `/start`: Botu başlatır ve hoş geldin mesajı gönderir
- `/setlang`: Dil ayarlarını değiştirir

## Katkıda Bulunma

1. Fork yapın
2. Yeni bir branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'inizi push edin (`git push origin feature/AmazingFeature`)
5. Bir Pull Request açın

## Lisans

MIT Lisansı altında dağıtılmaktadır. Detaylar için `LICENSE` dosyasına bakın.

## İletişim

- Geliştirici: Stixyie
- Proje Linki: [GitHub Deposu](https://github.com/Stixyie/Nyxie-Protogen-Chatbot-Telegram)

## Teşekkürler

Bu projenin geliştirilmesinde emeği geçen herkese teşekkür ederim özelikle google gemini ve google cloud'a! 
