# Bilgi Yarışması Uygulaması

Bu, Python ile geliştirilmiş bir bilgi yarışması masaüstü uygulamasıdır. Kullanıcılar çeşitli kategorilerde sorulara cevap vererek puan kazanabilir ve yüksek skorlar elde edebilirler.

## Özellikler

- Farklı kategorilerde sorular (Genel Kültür, Bilim, Tarih, Spor, Sanat)
- Zamana karşı yarışma
- Puanlama sistemi
- Yüksek skor tablosu
- Kullanıcı dostu arayüz

## Gereksinimler

- Python 3.8 veya üzeri
- Tkinter (Python ile genellikle birlikte gelir)
- SQLite3 (Python ile genellikle birlikte gelir)

## Kurulum

1. Bu repoyu klonlayın veya ZIP olarak indirin.
2. Gerekli bağımlılıkları yükleyin:
   ```
   pip install -r requirements.txt
   ```
3. Uygulamayı çalıştırın:
   ```
   python main.py
   ```

## Kullanım

1. Uygulamayı başlattığınızda ana menü görüntülenecektir.
2. "Oyuna Başla" butonuna tıklayarak kategori seçim ekranına geçebilirsiniz.
3. Bir kategori seçtikten sonra, sorular gösterilmeye başlayacaktır.
4. Her soru için 30 saniye süreniz vardır.
5. Doğru cevaplar için puan kazanırsınız (kalan süreye göre bonus puan eklenir).
6. Oyun bittiğinde, isminizi girerek skorunuzu kaydedebilirsiniz.
7. Yüksek skorlar bölümünden en iyi 10 skoru görebilirsiniz.

## Soru Bankası

Varsayılan olarak, uygulama 25 adet örnek soru içerir. Kendi sorularınızı eklemek için `questions.json` dosyasını düzenleyebilirsiniz.

## Lisans

Bu proje açık kaynak olarak MIT lisansı altında lisanslanmıştır. 