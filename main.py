#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sqlite3
from datetime import datetime
import random
import socketio

class BilgiYarismasi:
    def __init__(self, root):
        self.root = root
        self.root.title("Bilgi Yarışması")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Ağ bağlantısı için değişkenler
        self.connected = False
        self.room_code = None
        self.teams = []
        self.is_host = False
        
        # Tema değişkenleri - Sadece gündüz modu
        self.theme = {
            "bg": "#f0f0f0",
            "fg": "black",
            "button_bg": "#2196F3",
            "button_fg": "black"
        }
        
        # Tema ve stil ayarları
        self.style = ttk.Style()
        self.apply_theme()
        
        # Veritabanı kontrolü ve oluşturma
        self.check_database()
        
        # Değişkenleri başlat
        self.current_question = 0
        self.score = 0
        self.question_time = 30  # Varsayılan soru süresi
        self.time_left = self.question_time
        self.timer_running = False
        self.questions = []
        self.language = "Türkçe"  # Varsayılan dil
        
        # Ayarları yükle
        self.load_settings()
        
        # Ana ekranı göster
        self.show_main_menu()
        
        # Socket.IO bağlantısı
        self.sio = socketio.Client()
        try:
            self.sio.connect('http://192.168.1.102:8080')  # Gateway IP adresi
            self.connected = True
            print("Sunucuya başarıyla bağlanıldı.")
        except Exception as e:
            messagebox.showwarning("Bağlantı Hatası", "Sunucuya bağlanılamadı. Çevrimdışı modda devam ediliyor.")
            print(f"Bağlantı hatası: {e}")
            self.connected = False
    
    def apply_theme(self):
        """Temayı uygular."""
        self.style.configure("TFrame", background=self.theme["bg"])
        self.style.configure("TButton", padding=6, relief="flat", background=self.theme["button_bg"], foreground=self.theme["button_fg"])
        self.style.configure("TLabel", background=self.theme["bg"], font=('Arial', 11), foreground=self.theme["fg"])
        self.style.configure("TEntry", fieldbackground=self.theme["bg"], foreground=self.theme["fg"])
        self.style.configure("TSpinbox", fieldbackground=self.theme["bg"], foreground=self.theme["fg"])
        
        # Treeview (skor tablosu) için özel stil
        self.style.configure("Treeview", 
                             background=self.theme["bg"], 
                             fieldbackground=self.theme["bg"], 
                             foreground=self.theme["fg"])
        self.style.map("Treeview", 
                      background=[('selected', self.theme["button_bg"])],
                      foreground=[('selected', self.theme["button_fg"])])
        
        self.style.configure("Treeview.Heading", 
                             background=self.theme["button_bg"], 
                             foreground=self.theme["button_fg"],
                             font=('Arial', 10, 'bold'))
        
        # Özel buton stilleri
        self.style.configure("Correct.TButton", 
                             background="green", 
                             foreground="white")
        self.style.configure("Wrong.TButton", 
                             background="red", 
                             foreground="white")
        
        # Kök pencere arka plan rengini güncelle
        self.root.configure(background=self.theme["bg"])
    
    def check_database(self):
        """Veritabanının varlığını kontrol eder ve yoksa oluşturur."""
        if not os.path.exists("quiz_data.db"):
            conn = sqlite3.connect("quiz_data.db")
            cur = conn.cursor()
            
            # Sorular tablosu
            cur.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                category TEXT,
                difficulty TEXT,
                question TEXT,
                correct_answer TEXT,
                option1 TEXT,
                option2 TEXT,
                option3 TEXT,
                option4 TEXT
            )
            ''')
            
            # Yüksek skorlar tablosu
            cur.execute('''
            CREATE TABLE IF NOT EXISTS high_scores (
                id INTEGER PRIMARY KEY,
                player_name TEXT,
                score INTEGER,
                date TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            
            # Örnek soruları yükle
            self.load_sample_questions()
    
    def load_sample_questions(self):
        """Örnek soruları JSON dosyasından yükler."""
        try:
            if os.path.exists("questions.json"):
                with open("questions.json", "r", encoding="utf-8") as file:
                    questions = json.load(file)
                    
                    conn = sqlite3.connect("quiz_data.db")
                    cur = conn.cursor()
                    
                    for q in questions:
                        cur.execute(
                            "INSERT INTO questions (category, difficulty, question, correct_answer, option1, option2, option3, option4) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (q["category"], q["difficulty"], q["question"], q["correct_answer"], 
                             q["options"][0], q["options"][1], q["options"][2], q["options"][3])
                        )
                    
                    conn.commit()
                    conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Sorular yüklenirken hata oluştu: {e}")
    
    def show_main_menu(self):
        """Ana menüyü gösterir."""
        # Önceki widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="BİLGİ YARIŞMASI", font=("Arial", 24, "bold"))
        title_label.pack(pady=30)
        
        # Menü butonları
        btn_play = ttk.Button(main_frame, text="Oyuna Başla", command=self.show_team_name_screen, width=20)
        btn_play.pack(pady=10)
        
        btn_highscores = ttk.Button(main_frame, text="Yüksek Skorlar", command=self.show_high_scores, width=20)
        btn_highscores.pack(pady=10)
        
        btn_settings = ttk.Button(main_frame, text="Ayarlar", command=self.show_settings, width=20)
        btn_settings.pack(pady=10)
        
        btn_exit = ttk.Button(main_frame, text="Çıkış", command=self.root.quit, width=20)
        btn_exit.pack(pady=10)
    
    def show_team_name_screen(self):
        """Takım ismi girme ekranını gösterir."""
        # Önceki widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Takım ismi çerçevesi
        team_frame = ttk.Frame(self.root)
        team_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ttk.Label(
            team_frame, 
            text="TAKIM İSMİNİZİ GİRİN", 
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=30)
        
        # Takım ismi girişi
        name_frame = ttk.Frame(team_frame)
        name_frame.pack(pady=20)
        
        name_label = ttk.Label(
            name_frame, 
            text="Takım İsmi:", 
            font=("Arial", 12)
        )
        name_label.pack(side="left", padx=5)
        
        self.team_name = tk.StringVar()
        name_entry = ttk.Entry(
            name_frame, 
            textvariable=self.team_name, 
            width=20,
            font=("Arial", 12)
        )
        name_entry.pack(side="left", padx=5)
        name_entry.focus()
        
        # Oda oluştur/katıl seçenekleri
        options_frame = ttk.Frame(team_frame)
        options_frame.pack(pady=20)
        
        create_btn = ttk.Button(
            options_frame,
            text="Oda Oluştur",
            command=self.create_room,
            width=20
        )
        create_btn.pack(pady=10)
        
        # Oda kodu girişi
        join_frame = ttk.Frame(team_frame)
        join_frame.pack(pady=10)
        
        code_label = ttk.Label(
            join_frame,
            text="Oda Kodu:",
            font=("Arial", 12)
        )
        code_label.pack(side="left", padx=5)
        
        self.room_code_var = tk.StringVar()
        code_entry = ttk.Entry(
            join_frame,
            textvariable=self.room_code_var,
            width=10,
            font=("Arial", 12)
        )
        code_entry.pack(side="left", padx=5)
        
        join_btn = ttk.Button(
            join_frame,
            text="Odaya Katıl",
            command=self.join_room,
            width=15
        )
        join_btn.pack(side="left", padx=5)
        
        # Geri butonu
        back_btn = ttk.Button(
            team_frame,
            text="Ana Menüye Dön",
            command=self.show_main_menu,
            width=20
        )
        back_btn.pack(pady=20)

    def create_room(self):
        """Yeni bir oda oluşturur ve lobi ekranına geçer."""
        team_name = self.team_name.get().strip()
        if not team_name:
            messagebox.showwarning("Uyarı", "Lütfen bir takım ismi girin.")
            return
            
        # TODO: Sunucu bağlantısı yapılacak
        self.is_host = True
        self.room_code = "".join([str(random.randint(0, 9)) for _ in range(6)])  # Geçici kod
        self.teams = [{"name": team_name, "is_host": True, "ready": False}]
        self.show_lobby()

    def join_room(self):
        """Var olan bir odaya katılır."""
        team_name = self.team_name.get().strip()
        room_code = self.room_code_var.get().strip()
        
        if not team_name:
            messagebox.showwarning("Uyarı", "Lütfen bir takım ismi girin.")
            return
            
        if not room_code:
            messagebox.showwarning("Uyarı", "Lütfen oda kodunu girin.")
            return
            
        # TODO: Sunucu bağlantısı yapılacak
        self.room_code = room_code
        self.teams = [
            {"name": "Ev Sahibi Takım", "is_host": True, "ready": False},
            {"name": team_name, "is_host": False, "ready": False}
        ]
        self.show_lobby()

    def show_lobby(self):
        """Lobi ekranını gösterir."""
        # Önceki widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Lobi çerçevesi
        lobby_frame = ttk.Frame(self.root)
        lobby_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Üst bilgi çerçevesi
        info_frame = ttk.Frame(lobby_frame)
        info_frame.pack(fill="x", pady=10)
        
        # Oda kodu
        code_label = ttk.Label(
            info_frame,
            text=f"Oda Kodu: {self.room_code}",
            font=("Arial", 14, "bold")
        )
        code_label.pack(side="left", padx=5)
        
        # Kopyala butonu
        copy_btn = ttk.Button(
            info_frame,
            text="Kopyala",
            command=lambda: self.root.clipboard_append(self.room_code),
            width=10
        )
        copy_btn.pack(side="left", padx=5)
        
        # Takımlar listesi
        teams_frame = ttk.LabelFrame(lobby_frame, text="Takımlar")
        teams_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Takımları listele
        self.teams_list = ttk.Treeview(
            teams_frame,
            columns=("Takım", "Durum"),
            show="headings",
            height=10
        )
        
        self.teams_list.heading("Takım", text="Takım")
        self.teams_list.heading("Durum", text="Durum")
        
        self.teams_list.column("Takım", width=200)
        self.teams_list.column("Durum", width=100)
        
        for team in self.teams:
            status = "Hazır" if team["ready"] else "Bekliyor"
            host_mark = "👑 " if team["is_host"] else ""
            self.teams_list.insert("", "end", values=(f"{host_mark}{team['name']}", status))
        
        self.teams_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Alt butonlar çerçevesi
        buttons_frame = ttk.Frame(lobby_frame)
        buttons_frame.pack(fill="x", pady=10)
        
        # Hazır/Başlat butonu
        if self.is_host:
            start_btn = ttk.Button(
                buttons_frame,
                text="Oyunu Başlat",
                command=self.start_game_from_lobby,
                width=20
            )
            start_btn.pack(side="left", padx=5)
        else:
            ready_btn = ttk.Button(
                buttons_frame,
                text="Hazır",
                command=self.toggle_ready,
                width=20
            )
            ready_btn.pack(side="left", padx=5)
        
        # Odadan Ayrıl butonu
        leave_btn = ttk.Button(
            buttons_frame,
            text="Odadan Ayrıl",
            command=self.leave_room,
            width=20
        )
        leave_btn.pack(side="right", padx=5)
        
        # Sohbet alanı
        chat_frame = ttk.LabelFrame(lobby_frame, text="Sohbet")
        chat_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.chat_text = tk.Text(chat_frame, height=8, width=50)
        self.chat_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        chat_input_frame = ttk.Frame(chat_frame)
        chat_input_frame.pack(fill="x", padx=5, pady=5)
        
        self.chat_input = ttk.Entry(chat_input_frame)
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        send_btn = ttk.Button(
            chat_input_frame,
            text="Gönder",
            command=self.send_chat_message,
            width=10
        )
        send_btn.pack(side="right")
        
        # Lobi güncellemelerini başlat
        self.update_lobby()

    def toggle_ready(self):
        """Hazır durumunu değiştirir."""
        # TODO: Sunucuya hazır durumu gönderilecek
        for team in self.teams:
            if team["name"] == self.team_name.get():
                team["ready"] = not team["ready"]
                break
        self.update_lobby()

    def start_game_from_lobby(self):
        """Lobiden oyunu başlatır."""
        # Tüm oyuncuların hazır olup olmadığını kontrol et
        if not all(team["ready"] or team["is_host"] for team in self.teams):
            messagebox.showwarning("Uyarı", "Tüm oyuncular hazır değil!")
            return
            
        # TODO: Sunucuya oyun başlatma sinyali gönderilecek
        self.start_game("Genel Kültür")

    def leave_room(self):
        """Odadan ayrılır."""
        if messagebox.askyesno("Emin misiniz?", "Odadan ayrılmak istediğinize emin misiniz?"):
            # TODO: Sunucuya ayrılma sinyali gönderilecek
            self.show_main_menu()

    def send_chat_message(self):
        """Sohbet mesajı gönderir."""
        message = self.chat_input.get().strip()
        if message:
            # TODO: Sunucuya mesaj gönderilecek
            self.chat_text.insert("end", f"{self.team_name.get()}: {message}\n")
            self.chat_text.see("end")
            self.chat_input.delete(0, "end")

    def update_lobby(self):
        """Lobi bilgilerini günceller."""
        # TODO: Sunucudan güncel bilgileri al
        # Şimdilik sadece arayüzü güncelle
        self.teams_list.delete(*self.teams_list.get_children())
        for team in self.teams:
            status = "Hazır" if team["ready"] else "Bekliyor"
            host_mark = "👑 " if team["is_host"] else ""
            self.teams_list.insert("", "end", values=(f"{host_mark}{team['name']}", status))
        
        # Her 1 saniyede bir güncelle
        self.root.after(1000, self.update_lobby)
    
    def show_category_selection(self):
        """Kategori seçim ekranını gösterir."""
        # Önceki widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Kategori seçim çerçevesi
        category_frame = ttk.Frame(self.root)
        category_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ttk.Label(category_frame, text="KATEGORİ SEÇİMİ", font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # Veritabanından kategorileri getir
        categories = self.get_categories()
        
        # Kategori butonları
        for category in categories:
            btn_category = ttk.Button(
                category_frame, 
                text=category, 
                command=lambda cat=category: self.start_game(cat),
                width=20
            )
            btn_category.pack(pady=5)
        
        # Geri butonu
        btn_back = ttk.Button(category_frame, text="Ana Menüye Dön", command=self.show_main_menu, width=20)
        btn_back.pack(pady=20)
    
    def get_categories(self):
        """Veritabanından kategorileri getirir."""
        conn = sqlite3.connect("quiz_data.db")
        cur = conn.cursor()
        
        cur.execute("SELECT DISTINCT category FROM questions")
        categories = [row[0] for row in cur.fetchall()]
        
        conn.close()
        
        # Eğer veritabanında kategori yoksa, varsayılan kategorileri döndür
        if not categories:
            categories = ["Genel Kültür", "Bilim", "Tarih", "Spor", "Sanat"]
        
        return categories
    
    def start_game(self, category):
        """Seçilen kategoride oyunu başlatır."""
        # Soruları veritabanından al
        self.load_questions(category)
        
        if not self.questions:
            messagebox.showinfo("Bilgi", "Bu kategoride soru bulunamadı.")
            self.show_main_menu()
            return
        
        # Oyun değişkenlerini sıfırla
        self.current_question = 0
        self.score = 0
        self.time_left = self.question_time
        
        # İlk soruyu göster
        self.show_question()
    
    def load_questions(self, category):
        """Seçilen kategorideki soruları veritabanından yükler."""
        conn = sqlite3.connect("quiz_data.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Kategori seçimi kaldırıldığı için tüm sorulardan rastgele seçim yapılacak
        cur.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 10")
        
        self.questions = []
        for row in cur.fetchall():
            question = dict(row)
            options = [
                question["option1"],
                question["option2"],
                question["option3"],
                question["option4"]
            ]
            self.questions.append({
                "question": question["question"],
                "options": options,
                "correct_answer": question["correct_answer"]
            })
        
        conn.close()
    
    def show_question(self):
        """Mevcut soruyu gösterir."""
        # Önceki widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Soru çerçevesi
        question_frame = ttk.Frame(self.root)
        question_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Üst bilgi çerçevesi
        info_frame = ttk.Frame(question_frame)
        info_frame.pack(fill="x", pady=10)
        
        # Soru numarası ve skor
        question_label = ttk.Label(
            info_frame, 
            text=f"Soru {self.current_question + 1}/{len(self.questions)}", 
            font=("Arial", 12)
        )
        question_label.pack(side="left")
        
        score_label = ttk.Label(
            info_frame, 
            text=f"Skor: {self.score}", 
            font=("Arial", 12)
        )
        score_label.pack(side="right")
        
        # Zaman sayacı
        self.timer_label = ttk.Label(
            question_frame, 
            text=f"Süre: {self.time_left} saniye", 
            font=("Arial", 12)
        )
        self.timer_label.pack(pady=10)
        
        # Soru metni
        question_text = ttk.Label(
            question_frame, 
            text=self.questions[self.current_question]["question"], 
            font=("Arial", 14, "bold"),
            wraplength=700
        )
        question_text.pack(pady=20)
        
        # Cevap seçenekleri
        options_frame = ttk.Frame(question_frame)
        options_frame.pack(fill="both", expand=True, pady=10)
        
        # Butonları saklamak için bir liste oluştur
        self.option_buttons = []
        
        options = self.questions[self.current_question]["options"]
        for i, option in enumerate(options):
            option_btn = ttk.Button(
                options_frame,
                text=option,
                command=lambda opt=option, btn_idx=i: self.check_answer(opt, btn_idx),
                width=40
            )
            option_btn.pack(pady=5)
            self.option_buttons.append(option_btn)
        
        # Sonuç mesajı için etiket
        self.result_label = ttk.Label(
            question_frame,
            text="",
            font=("Arial", 14, "bold")
        )
        self.result_label.pack(pady=10)
        
        # Devam butonu (başlangıçta gizli)
        self.continue_btn = ttk.Button(
            question_frame,
            text="Devam Et",
            command=self.next_question,
            width=20
        )
        
        # Zamanlayıcıyı başlat
        self.timer_running = True
        self.update_timer()
    
    def update_timer(self):
        """Zamanlayıcıyı günceller."""
        if self.timer_running and self.time_left > 0:
            self.time_left -= 1
            self.timer_label.config(text=f"Süre: {self.time_left} saniye")
            self.root.after(1000, self.update_timer)
        elif self.timer_running and self.time_left == 0:
            self.timer_running = False
            self.result_label.config(text="Süre doldu!")
            self.show_correct_answer()
            self.continue_btn.pack(pady=10)
    
    def check_answer(self, selected_option, button_index):
        """Seçilen cevabı kontrol eder."""
        self.timer_running = False
        
        correct_answer = self.questions[self.current_question]["correct_answer"]
        
        # Tüm butonları devre dışı bırak
        for btn in self.option_buttons:
            btn.configure(state="disabled")
        
        # Özel stil oluştur
        self.style.configure("Correct.TButton", background="green")
        self.style.configure("Wrong.TButton", background="red")
        
        if selected_option == correct_answer:
            # Doğru cevap - yeşil göster
            self.option_buttons[button_index].configure(style="Correct.TButton")
            self.score += 10 + self.time_left // 3  # Kalan zamana göre ek puan
            self.result_label.config(text=f"Tebrikler, doğru cevap! +{10 + self.time_left // 3} puan kazandınız.")
        else:
            # Yanlış cevap - kırmızı göster ve doğru cevabı bul
            self.option_buttons[button_index].configure(style="Wrong.TButton")
            self.result_label.config(text=f"Üzgünüm, yanlış cevap.")
            self.show_correct_answer()
        
        # Devam butonunu göster
        self.continue_btn.pack(pady=10)
    
    def show_correct_answer(self):
        """Doğru cevabı gösterir."""
        correct_answer = self.questions[self.current_question]["correct_answer"]
        
        # Doğru cevabı bul ve yeşil göster
        for i, option in enumerate(self.questions[self.current_question]["options"]):
            if option == correct_answer:
                self.option_buttons[i].configure(style="Correct.TButton")
                break
    
    def next_question(self):
        """Bir sonraki soruya geçer veya oyunu bitirir."""
        self.current_question += 1
        
        if self.current_question < len(self.questions):
            self.time_left = self.question_time
            self.show_question()
        else:
            self.end_game()
    
    def end_game(self):
        """Oyunu bitirir ve sonuçları gösterir."""
        # Önceki widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Sonuç çerçevesi
        result_frame = ttk.Frame(self.root)
        result_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Sonuç başlığı
        title_label = ttk.Label(
            result_frame, 
            text="OYUN BİTTİ", 
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=20)
        
        # Takım ismi
        team_label = ttk.Label(
            result_frame, 
            text=f"Takım: {self.team_name.get()}", 
            font=("Arial", 14)
        )
        team_label.pack(pady=10)
        
        # Skor
        score_label = ttk.Label(
            result_frame, 
            text=f"Toplam Skorunuz: {self.score}", 
            font=("Arial", 16)
        )
        score_label.pack(pady=10)
        
        # Skoru kaydet butonu
        save_btn = ttk.Button(
            result_frame, 
            text="Skoru Kaydet", 
            command=self.save_score,
            width=20
        )
        save_btn.pack(pady=20)
        
        # Ana menüye dön butonu
        menu_btn = ttk.Button(
            result_frame, 
            text="Ana Menüye Dön", 
            command=self.show_main_menu,
            width=20
        )
        menu_btn.pack(pady=10)
    
    def save_score(self):
        """Takımın skorunu veritabanına kaydeder."""
        team_name = self.team_name.get().strip()
        
        conn = sqlite3.connect("quiz_data.db")
        cur = conn.cursor()
        
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute(
            "INSERT INTO high_scores (player_name, score, date) VALUES (?, ?, ?)",
            (team_name, self.score, current_date)
        )
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Başarılı", "Skorunuz kaydedildi!")
        self.show_high_scores()
    
    def show_high_scores(self):
        """Yüksek skorlar listesini gösterir."""
        # Önceki widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Yüksek skorlar çerçevesi
        scores_frame = ttk.Frame(self.root)
        scores_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ttk.Label(
            scores_frame, 
            text="YÜKSEK SKORLAR", 
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=20)
        
        # Skorları veritabanından al
        conn = sqlite3.connect("quiz_data.db")
        cur = conn.cursor()
        
        cur.execute("SELECT player_name, score, date FROM high_scores ORDER BY score DESC LIMIT 10")
        high_scores = cur.fetchall()
        
        conn.close()
        
        # Tablo çerçevesi
        table_frame = ttk.Frame(scores_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tablo oluştur
        columns = ("Sıra", "İsim", "Skor", "Tarih")
        
        score_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10, style="Treeview")
        score_tree.tag_configure('evenrow', background=self.theme["bg"])
        score_tree.tag_configure('oddrow', background=self.theme["bg"])
        score_tree.pack(side="left", fill="both", expand=True)
        
        # Sütun başlıkları
        for col in columns:
            score_tree.heading(col, text=col)
        
        # Sütun genişlikleri
        score_tree.column("Sıra", width=50, anchor="center")
        score_tree.column("İsim", width=200, anchor="w")
        score_tree.column("Skor", width=100, anchor="center")
        score_tree.column("Tarih", width=150, anchor="center")
        
        # Skorları ekle - Satır renklerini ayarla
        for i, (name, score, date) in enumerate(high_scores, 1):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            score_tree.insert("", "end", values=(i, name, score, date), tags=(tag,))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=score_tree.yview)
        score_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Ana menüye dön butonu
        menu_btn = ttk.Button(
            scores_frame, 
            text="Ana Menüye Dön", 
            command=self.show_main_menu,
            width=20
        )
        menu_btn.pack(pady=20)
    
    def show_settings(self):
        """Ayarlar ekranını gösterir."""
        # Önceki widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ayarlar çerçevesi
        settings_frame = ttk.Frame(self.root)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ttk.Label(
            settings_frame, 
            text="AYARLAR", 
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=20)
        
        # Notebook (sekmeli arayüz) oluştur
        notebook = ttk.Notebook(settings_frame)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Genel ayarlar sekmesi
        general_tab = ttk.Frame(notebook)
        notebook.add(general_tab, text="Genel Ayarlar")
        
        # Soru ekleme sekmesi
        question_tab = ttk.Frame(notebook)
        notebook.add(question_tab, text="Admin Paneli")
        
        # Genel ayarlar içeriği
        # Dil seçimi
        lang_frame = ttk.Frame(general_tab)
        lang_frame.pack(pady=20, fill="x")
        
        lang_label = ttk.Label(
            lang_frame, 
            text="Dil:", 
            font=("Arial", 12)
        )
        lang_label.pack(side="left", padx=5)
        
        self.lang_var = tk.StringVar(value=self.language)
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=["Türkçe", "English"],
            width=10,
            font=("Arial", 12),
            state="readonly"
        )
        lang_combo.pack(side="left", padx=5)
        
        # Ayarları kaydet butonu
        save_btn = ttk.Button(
            general_tab, 
            text="Ayarları Kaydet", 
            command=self.update_settings,
            width=20
        )
        save_btn.pack(pady=20)
        
        # Admin paneli içeriği
        # Admin şifre kontrolü
        admin_frame = ttk.Frame(question_tab)
        admin_frame.pack(fill="x", padx=10, pady=20)
        
        admin_label = ttk.Label(
            admin_frame,
            text="Admin Şifresi:",
            font=("Arial", 12)
        )
        admin_label.pack(side="left", padx=5)
        
        self.admin_password = tk.StringVar()
        admin_entry = ttk.Entry(
            admin_frame,
            textvariable=self.admin_password,
            width=20,
            font=("Arial", 12),
            show="*"  # Şifreyi gizle
        )
        admin_entry.pack(side="left", padx=5)
        
        admin_login_btn = ttk.Button(
            admin_frame,
            text="Giriş",
            command=self.verify_admin,
            width=10
        )
        admin_login_btn.pack(side="left", padx=5)
        
        # Admin paneli (başlangıçta gizli)
        self.admin_panel_frame = ttk.Frame(question_tab)
        
        # Ana menüye dön butonu
        menu_btn = ttk.Button(
            settings_frame, 
            text="Ana Menüye Dön", 
            command=self.show_main_menu,
            width=20
        )
        menu_btn.pack(pady=10)
        
        # Geri çıkma butonu
        back_btn = ttk.Button(
            settings_frame, 
            text="Geri", 
            command=self.show_main_menu,
            width=20
        )
        back_btn.pack(pady=5)
    
    def verify_admin(self):
        """Admin şifresini doğrular."""
        # Gerçek uygulamada bu şifre güvenli bir şekilde saklanmalıdır
        # Örneğin, hash'lenmiş olarak veritabanında veya ayarlar dosyasında
        admin_password = "admin123"  # Örnek şifre
        
        if self.admin_password.get() == admin_password:
            # Şifre doğruysa admin panelini göster
            self.show_admin_panel()
        else:
            messagebox.showerror("Hata", "Yanlış admin şifresi!")
    
    def show_admin_panel(self):
        """Admin panelini gösterir."""
        # Önce paneli temizle
        for widget in self.admin_panel_frame.winfo_children():
            widget.destroy()
        
        # Paneli göster
        self.admin_panel_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Admin paneli sekmelerini oluştur
        admin_notebook = ttk.Notebook(self.admin_panel_frame)
        admin_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Soru ayarları sekmesi
        settings_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(settings_tab, text="Oyun Ayarları")
        
        # Soru ekleme sekmesi
        question_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(question_tab, text="Soru Ekle")
        
        # Oyun ayarları içeriği
        # Soru süresi ayarı
        time_frame = ttk.Frame(settings_tab)
        time_frame.pack(pady=20, fill="x")
        
        time_label = ttk.Label(
            time_frame, 
            text="Soru Süresi (saniye):", 
            font=("Arial", 12)
        )
        time_label.pack(side="left", padx=5)
        
        self.time_var = tk.StringVar(value=str(self.question_time))
        time_entry = ttk.Spinbox(
            time_frame,
            from_=10,
            to=60,
            textvariable=self.time_var,
            width=5,
            font=("Arial", 12)
        )
        time_entry.pack(side="left", padx=5)
        
        # Oyun ayarlarını kaydet butonu
        save_game_settings_btn = ttk.Button(
            settings_tab, 
            text="Oyun Ayarlarını Kaydet", 
            command=self.update_game_settings,
            width=25
        )
        save_game_settings_btn.pack(pady=20)
        
        # Soru ekleme içeriği
        # Soru metni
        question_label = ttk.Label(
            question_tab, 
            text="Soru:", 
            font=("Arial", 12)
        )
        question_label.pack(anchor="w", padx=10, pady=5)
        
        self.new_question = tk.StringVar()
        question_entry = ttk.Entry(
            question_tab,
            textvariable=self.new_question,
            width=60,
            font=("Arial", 12)
        )
        question_entry.pack(fill="x", padx=10, pady=5)
        
        # Kategori
        category_label = ttk.Label(
            question_tab, 
            text="Kategori:", 
            font=("Arial", 12)
        )
        category_label.pack(anchor="w", padx=10, pady=5)
        
        self.new_category = tk.StringVar(value="Genel Kültür")
        category_entry = ttk.Entry(
            question_tab,
            textvariable=self.new_category,
            width=30,
            font=("Arial", 12)
        )
        category_entry.pack(fill="x", padx=10, pady=5)
        
        # Zorluk seviyesi
        difficulty_label = ttk.Label(
            question_tab, 
            text="Zorluk:", 
            font=("Arial", 12)
        )
        difficulty_label.pack(anchor="w", padx=10, pady=5)
        
        self.new_difficulty = tk.StringVar(value="Orta")
        difficulty_combo = ttk.Combobox(
            question_tab,
            textvariable=self.new_difficulty,
            values=["Kolay", "Orta", "Zor"],
            width=15,
            font=("Arial", 12)
        )
        difficulty_combo.pack(fill="x", padx=10, pady=5)
        
        # Şıklar
        options_frame = ttk.LabelFrame(question_tab, text="Şıklar")
        options_frame.pack(fill="x", padx=10, pady=10)
        
        self.option_vars = []
        self.option_entries = []
        
        for i in range(4):
            option_frame = ttk.Frame(options_frame)
            option_frame.pack(fill="x", padx=5, pady=5)
            
            option_label = ttk.Label(
                option_frame, 
                text=f"{chr(65+i)})", 
                font=("Arial", 12)
            )
            option_label.pack(side="left", padx=5)
            
            option_var = tk.StringVar()
            option_entry = ttk.Entry(
                option_frame,
                textvariable=option_var,
                width=50,
                font=("Arial", 12)
            )
            option_entry.pack(side="left", fill="x", expand=True, padx=5)
            
            self.option_vars.append(option_var)
            self.option_entries.append(option_entry)
        
        # Doğru cevap seçimi
        correct_frame = ttk.Frame(question_tab)
        correct_frame.pack(fill="x", padx=10, pady=10)
        
        correct_label = ttk.Label(
            correct_frame, 
            text="Doğru Cevap:", 
            font=("Arial", 12)
        )
        correct_label.pack(side="left", padx=5)
        
        self.correct_var = tk.StringVar(value="A")
        correct_combo = ttk.Combobox(
            correct_frame,
            textvariable=self.correct_var,
            values=["A", "B", "C", "D"],
            width=5,
            font=("Arial", 12)
        )
        correct_combo.pack(side="left", padx=5)
        
        # Doğru cevap yanına kaydet butonu
        save_question_btn = ttk.Button(
            correct_frame, 
            text="Soruyu Kaydet", 
            command=self.add_question,
            width=20
        )
        save_question_btn.pack(side="left", padx=20)
        
        # Butonlar için çerçeve
        buttons_frame = ttk.Frame(question_tab)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        # Formu temizle butonu
        clear_btn = ttk.Button(
            buttons_frame, 
            text="Formu Temizle", 
            command=self.clear_question_form,
            width=20
        )
        clear_btn.pack(side="left", padx=5, pady=10)
    
    def update_game_settings(self):
        """Oyun ayarlarını günceller ve kaydeder."""
        try:
            new_time = int(self.time_var.get())
            if new_time < 10:
                new_time = 10
            elif new_time > 60:
                new_time = 60
                
            self.question_time = new_time
            self.save_settings()
            messagebox.showinfo("Başarılı", "Oyun ayarları kaydedildi!")
        except ValueError:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir sayı girin.")
    
    def add_question(self):
        """Yeni soruyu veritabanına ekler."""
        # Form alanlarını kontrol et
        question_text = self.new_question.get().strip()
        category = self.new_category.get().strip()
        difficulty = self.new_difficulty.get()
        
        options = [var.get().strip() for var in self.option_vars]
        correct_index = ord(self.correct_var.get()) - 65  # A=0, B=1, C=2, D=3
        
        # Boş alan kontrolü
        if not question_text:
            messagebox.showwarning("Uyarı", "Lütfen soru metnini girin.")
            return
        
        if not category:
            messagebox.showwarning("Uyarı", "Lütfen kategori girin.")
            return
        
        # Şıkların boş olup olmadığını kontrol et
        empty_options = [i for i, opt in enumerate(options) if not opt]
        if empty_options:
            option_letters = [chr(65 + i) for i in empty_options]
            messagebox.showwarning("Uyarı", f"Lütfen şu şıkları doldurun: {', '.join(option_letters)}")
            return
        
        # Doğru cevabı al
        correct_answer = options[correct_index]
        
        try:
            # Veritabanına ekle
            conn = sqlite3.connect("quiz_data.db")
            cur = conn.cursor()
            
            cur.execute(
                "INSERT INTO questions (category, difficulty, question, correct_answer, option1, option2, option3, option4) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (category, difficulty, question_text, correct_answer, options[0], options[1], options[2], options[3])
            )
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Başarılı", "Soru başarıyla eklendi!")
            
            # Formu temizle
            self.clear_question_form()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Soru eklenirken hata oluştu: {e}")
    
    def clear_question_form(self):
        """Soru formunu temizler."""
        self.new_question.set("")
        self.new_category.set("Genel Kültür")
        self.new_difficulty.set("Orta")
        self.correct_var.set("A")
        
        # Şıkları temizle
        for var in self.option_vars:
            var.set("")
    
    def update_settings(self):
        """Ayarları günceller ve kaydeder."""
        try:
            self.language = self.lang_var.get()
            
            self.save_settings()
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi!")
            self.show_main_menu()
        except ValueError:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir sayı girin.")
    
    def load_settings(self):
        """Ayarları yükler veya varsayılan ayarları oluşturur."""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as file:
                    settings = json.load(file)
                    self.question_time = settings.get("question_time", 30)
                    self.language = settings.get("language", "Türkçe")
            else:
                # Varsayılan ayarları oluştur
                self.save_settings()
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar yüklenirken hata oluştu: {e}")
    
    def save_settings(self):
        """Ayarları kaydeder."""
        settings = {
            "question_time": self.question_time,
            "language": self.language
        }
        
        try:
            with open("settings.json", "w", encoding="utf-8") as file:
                json.dump(settings, file, indent=4)
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar kaydedilirken hata oluştu: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BilgiYarismasi(root)
    root.mainloop() 