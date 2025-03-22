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
        
        # Socket.IO istemcisini başlat
        self.sio = socketio.Client()
        self.setup_socket_events()
        
        # Ağ bağlantısı için değişkenler
        self.connected = False
        self.room_code = None
        self.teams = []
        self.is_host = False
        
        # Tema değişkenleri
        self.theme = {
            "bg": "#f0f0f0",
            "fg": "black",
            "button_bg": "#2196F3",
            "button_fg": "black"
        }
        
        # Tema ve stil ayarları
        self.style = ttk.Style()
        self.apply_theme()
        
        # Değişkenleri başlat
        self.current_question = 0
        self.score = 0
        self.question_time = 30
        self.time_left = self.question_time
        self.timer_running = False
        self.questions = []
        
        try:
            # Sunucuya bağlan
            self.sio.connect('http://192.168.1.103:8080', wait_timeout=10)
            self.connected = True
        except Exception as e:
            print(f"Bağlantı hatası: {str(e)}")
            messagebox.showerror("Bağlantı Hatası", "Sunucuya bağlanılamadı! Çevrimdışı modda devam ediliyor.")
            self.connected = False
        
        # Ana ekranı göster
        self.show_main_menu()
    
    def setup_socket_events(self):
        """Socket.IO event dinleyicilerini ayarlar."""
        @self.sio.on('connect')
        def on_connect():
            print("Sunucuya bağlanıldı!")
            self.connected = True
        
        @self.sio.on('disconnect')
        def on_disconnect():
            print("Sunucu bağlantısı kesildi!")
            self.connected = False
        
        @self.sio.on('error')
        def on_error(data):
            messagebox.showerror("Hata", data['message'])
        
        @self.sio.on('room_created')
        def on_room_created(data):
            self.room_code = data['room_code']
            self.teams = data['teams']
            self.show_lobby()
        
        @self.sio.on('room_updated')
        def on_room_updated(data):
            self.teams = data['teams']
            self.update_lobby_ui()
        
        @self.sio.on('game_started')
        def on_game_started(data):
            self.show_question(data['first_question'])
        
        @self.sio.on('show_question')
        def on_show_question(data):
            self.show_question(data)
        
        @self.sio.on('show_results')
        def on_show_results(data):
            correct_answer = data['correct_answer']
            scores = data['scores']
            self.show_results(correct_answer, scores)
        
        @self.sio.on('game_over')
        def on_game_over(data):
            scores = data['scores']
            messagebox.showinfo("Oyun Bitti!", f"Final puanları:\n{scores}")
            self.show_main_menu()
        
        @self.sio.on('new_chat_message')
        def on_new_chat_message(data):
            if hasattr(self, 'chat_text'):
                self.chat_text.insert("end", f"{data['team_name']}: {data['message']}\n")
                self.chat_text.see("end")
        
        @self.sio.on('teams_updated')
        def on_teams_updated(data):
            print(f"Takımlar güncellendi: {data['teams']}")
            self.teams = data['teams']
            if hasattr(self, 'teams_list'):
                self.update_teams_list()
        
    def create_room(self):
        """Yeni bir oda oluşturur."""
        team_name = self.team_name.get().strip()
        if not team_name:
            messagebox.showwarning("Uyarı", "Lütfen bir takım ismi girin.")
            return
        
        self.is_host = True
        self.sio.emit('create_room', {'team_name': team_name})
    
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
        
        self.sio.emit('join_room', {
            'team_name': team_name,
            'room_code': room_code
        })
    
    def toggle_ready(self):
        """Hazır durumunu değiştirir."""
        self.sio.emit('toggle_ready', {
            'room_code': self.room_code,
            'team_name': self.team_name.get()
        })
    
    def start_game_from_lobby(self):
        """Lobiden oyunu başlatır."""
        self.sio.emit('start_game', {
            'room_code': self.room_code
        })
    
    def leave_room(self):
        """Odadan ayrılır."""
        if messagebox.askyesno("Emin misiniz?", "Odadan ayrılmak istediğinize emin misiniz?"):
            self.sio.emit('leave_room', {
                'room_code': self.room_code,
                'team_name': self.team_name.get()
            })
            self.show_main_menu()
    
    def send_chat_message(self):
        """Sohbet mesajı gönderir."""
        message = self.chat_input.get().strip()
        if message:
            self.sio.emit('chat_message', {
                'room_code': self.room_code,
                'team_name': self.team_name.get(),
                'message': message
            })
            self.chat_input.delete(0, "end")
    
    def update_lobby_ui(self):
        """Lobi arayüzünü günceller."""
        if hasattr(self, 'teams_list'):
            self.teams_list.delete(*self.teams_list.get_children())
            for team in self.teams:
                status = "Hazır" if team["ready"] else "Bekliyor"
                host_mark = "👑 " if team["is_host"] else ""
                self.teams_list.insert("", "end", values=(f"{host_mark}{team['name']}", status))

    def apply_theme(self):
        """Tema ayarlarını uygular."""
        self.style.configure("TButton",
            padding=6,
            relief="flat",
            background=self.theme["button_bg"],
            foreground=self.theme["button_fg"])
        
        self.style.configure("TLabel",
            background=self.theme["bg"],
            foreground=self.theme["fg"])
        
        self.style.configure("TFrame",
            background=self.theme["bg"])
        
        self.style.configure("Treeview",
            background=self.theme["bg"],
            foreground=self.theme["fg"],
            fieldbackground=self.theme["bg"])
        
        # Doğru cevap stili
        self.style.configure("Correct.TRadiobutton",
            background=self.theme["bg"],
            foreground="green",
            font=("Helvetica", 10, "bold"))
        
        self.root.configure(bg=self.theme["bg"])

    def show_lobby(self):
        """Lobi ekranını gösterir."""
        # Mevcut widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Üst bilgi çerçevesi
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x", pady=10)
        
        # Oda kodu
        room_label = ttk.Label(info_frame, text=f"Oda Kodu: {self.room_code}", font=("Helvetica", 12))
        room_label.pack(side="left", padx=5)
        
        # Takımlar listesi
        self.teams_frame = ttk.Frame(main_frame)
        self.teams_frame.pack(fill="both", expand=True, pady=10)
        
        # Treeview
        columns = ("Takım", "Durum")
        self.teams_list = ttk.Treeview(self.teams_frame, columns=columns, show="headings")
        
        # Sütun başlıkları
        for col in columns:
            self.teams_list.heading(col, text=col)
            self.teams_list.column(col, width=100)
        
        self.teams_list.pack(fill="both", expand=True)
        
        # Takımları listele
        self.update_teams_list()
        
        # Kontrol butonları çerçevesi
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=10)
        
        # Hazır/Hazır Değil butonu (host değilse)
        if not self.is_host:
            ready_btn = ttk.Button(control_frame, text="Hazır/Hazır Değil", command=self.toggle_ready)
            ready_btn.pack(side="left", padx=5)
        
        # Oyunu Başlat butonu (host ise)
        if self.is_host:
            start_btn = ttk.Button(control_frame, text="Oyunu Başlat", command=self.start_game_from_lobby)
            start_btn.pack(side="left", padx=5)
        
        # Odadan Ayrıl butonu
        leave_btn = ttk.Button(control_frame, text="Odadan Ayrıl", command=self.leave_room)
        leave_btn.pack(side="right", padx=5)
        
        # Sohbet bölümü
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(fill="both", expand=True, pady=10)
        
        # Sohbet metni
        self.chat_text = tk.Text(chat_frame, height=10, width=50)
        self.chat_text.pack(fill="both", expand=True)
        
        # Mesaj girişi
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=5)
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side="left", fill="x", expand=True)
        
        send_btn = ttk.Button(input_frame, text="Gönder", command=self.send_chat_message)
        send_btn.pack(side="right", padx=5)

    def show_main_menu(self):
        """Ana menüyü gösterir."""
        # Mevcut widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Bilgi Yarışması", font=("Helvetica", 24, "bold"))
        title_label.pack(pady=20)
        
        # Çevrimiçi mod için frame
        if self.connected:
            online_frame = ttk.Frame(main_frame)
            online_frame.pack(pady=20)
            
            # Takım adı girişi
            team_label = ttk.Label(online_frame, text="Takım Adı:")
            team_label.pack()
            
            self.team_name = tk.StringVar()
            team_entry = ttk.Entry(online_frame, textvariable=self.team_name)
            team_entry.pack(pady=5)
            
            # Oda oluştur butonu
            create_room_btn = ttk.Button(online_frame, text="Oda Oluştur", command=self.create_room)
            create_room_btn.pack(pady=5)
            
            # Oda kodunu gir
            room_label = ttk.Label(online_frame, text="Oda Kodu:")
            room_label.pack()
            
            self.room_code_var = tk.StringVar()
            room_entry = ttk.Entry(online_frame, textvariable=self.room_code_var)
            room_entry.pack(pady=5)
            
            # Odaya katıl butonu
            join_room_btn = ttk.Button(online_frame, text="Odaya Katıl", command=self.join_room)
            join_room_btn.pack(pady=5)

    def start_game(self, category):
        """Oyunu başlatır."""
        # Mevcut widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Üst bilgi çerçevesi
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x", pady=10)
        
        # Kategori etiketi
        category_label = ttk.Label(info_frame, text=f"Kategori: {category}", font=("Helvetica", 12))
        category_label.pack(side="left", padx=5)
        
        # Skor etiketi
        score_label = ttk.Label(info_frame, text=f"Skor: {self.score}", font=("Helvetica", 12))
        score_label.pack(side="right", padx=5)
        
        # Soru çerçevesi
        question_frame = ttk.Frame(main_frame)
        question_frame.pack(fill="both", expand=True, pady=20)
        
        # Soru metni
        question_text = ttk.Label(question_frame, text=self.questions[0]['question'], 
                                wraplength=600, font=("Helvetica", 14))
        question_text.pack(pady=20)
        
        # Cevap butonları
        options = self.questions[0]['options']
        random.shuffle(options)
        
        for option in options:
            option_btn = ttk.Button(question_frame, text=option,
                                  command=lambda o=option: self.check_answer(o))
            option_btn.pack(pady=5, padx=20, fill="x")
        
        # Zamanlayıcı başlat
        self.time_left = self.question_time
        self.update_timer()

    def update_timer(self):
        """Süre sayacını günceller."""
        if hasattr(self, 'timer_label') and self.remaining_time > 0:
            self.timer_label.config(text=f"Süre: {self.remaining_time}")
            self.remaining_time -= 1
            self.root.after(1000, self.update_timer)
        elif self.remaining_time <= 0:
            # Süre dolduğunda sunucuya bildir
            self.sio.emit('time_up')
            # Cevap seçeneklerini devre dışı bırak ve doğru cevabı yeşil yap
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Frame):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ttk.Radiobutton):
                                    grandchild.configure(state='disabled')
                                    # Doğru cevabı yeşil yap
                                    if grandchild['text'].startswith(self.current_correct_answer):
                                        grandchild.configure(style='Correct.TRadiobutton')
            
            # 7 saniye bekle ve sonraki soruya geç
            self.root.after(7000, self.sio.emit, 'next_question')

    def check_answer(self, selected_answer):
        """Cevabı kontrol eder."""
        if not self.timer_running:
            return
        
        self.timer_running = False
        correct_answer = self.questions[0]['correct_answer']
        
        if selected_answer == correct_answer:
            self.score += 10
            messagebox.showinfo("Doğru!", "Tebrikler! Doğru cevap!")
        else:
            messagebox.showinfo("Yanlış!", f"Maalesef yanlış. Doğru cevap: {correct_answer}")
        
        # Sonraki soruya geç
        self.current_question += 1
        if self.current_question < len(self.questions):
            self.show_question()
        else:
            self.show_game_over()

    def show_question(self, question_data):
        """Soruyu gösterir."""
        # Mevcut widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Üst bilgi çerçevesi
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x", pady=10)
        
        # Soru numarası ve süre
        self.remaining_time = question_data.get('time', 30)  # Varsayılan 30 saniye
        self.timer_label = ttk.Label(info_frame, text=f"Süre: {self.remaining_time}", font=("Helvetica", 12))
        self.timer_label.pack(side="right", padx=5)
        
        question_num = ttk.Label(info_frame, text=f"Soru {question_data['question_number']}", font=("Helvetica", 12))
        question_num.pack(side="left", padx=5)
        
        # Soru metni
        question_frame = ttk.Frame(main_frame)
        question_frame.pack(fill="both", expand=True, pady=10)
        
        question_text = tk.Text(question_frame, height=4, wrap="word", font=("Helvetica", 12))
        question_text.insert("1.0", question_data['question'])
        question_text.configure(state="disabled")
        question_text.pack(fill="both", expand=True, padx=5)
        
        # Doğru cevabı sakla
        self.current_correct_answer = question_data['correct_answer']
        
        # Cevap seçenekleri
        answers_frame = ttk.Frame(main_frame)
        answers_frame.pack(fill="both", expand=True, pady=10)
        
        self.answer_var = tk.StringVar()
        for i, answer in enumerate(['A', 'B', 'C', 'D']):
            answer_text = question_data[f'answer_{answer.lower()}']
            rb = ttk.Radiobutton(
                answers_frame,
                text=f"{answer}) {answer_text}",
                value=answer,
                variable=self.answer_var,
                command=self.submit_answer
            )
            rb.pack(anchor="w", pady=5)
        
        # Süre sayacını başlat
        self.update_timer()

    def submit_answer(self):
        """Cevabı gönderir."""
        answer = self.answer_var.get()
        if answer:
            self.sio.emit('submit_answer', {
                'answer': answer,
                'team_name': self.team_name.get()
            })

    def show_game_over(self):
        """Oyun sonu ekranını gösterir."""
        # Mevcut widget'ları temizle
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Oyun sonu mesajı
        game_over_label = ttk.Label(main_frame, text="Oyun Bitti!", font=("Helvetica", 24, "bold"))
        game_over_label.pack(pady=20)
        
        # Final skor
        score_label = ttk.Label(main_frame, text=f"Final Skor: {self.score}", font=("Helvetica", 18))
        score_label.pack(pady=10)
        
        # Ana menüye dön butonu
        menu_btn = ttk.Button(main_frame, text="Ana Menüye Dön", command=self.show_main_menu)
        menu_btn.pack(pady=20)

    def update_teams_list(self):
        """Takım listesini güncelle"""
        if hasattr(self, 'teams_list'):
            # Mevcut takım listesini temizle
            for item in self.teams_list.get_children():
                self.teams_list.delete(item)
            
            # Yeni takım listesini oluştur
            for team in self.teams:
                status = "Hazır" if team.get('ready', False) else "Hazır Değil"
                host_mark = "👑 " if team.get('is_host', False) else ""
                self.teams_list.insert("", "end", values=(f"{host_mark}{team['name']}", status))

    def show_results(self, correct_answer, scores):
        """Sonuçları gösterir."""
        # Sonuç penceresi
        result_window = tk.Toplevel(self.root)
        result_window.title("Sonuçlar")
        result_window.geometry("400x300")
        
        # Doğru cevap
        correct_label = ttk.Label(result_window, text=f"Doğru Cevap: {correct_answer}", font=("Helvetica", 14, "bold"))
        correct_label.pack(pady=10)
        
        # Skor tablosu
        scores_frame = ttk.Frame(result_window)
        scores_frame.pack(fill="both", expand=True, pady=10)
        
        # Skor tablosu başlığı
        scores_label = ttk.Label(scores_frame, text="Skor Tablosu", font=("Helvetica", 12, "bold"))
        scores_label.pack(pady=5)
        
        # Skorları listele
        for team_name, score in scores.items():
            team_label = ttk.Label(scores_frame, text=f"{team_name}: {score} puan")
            team_label.pack(pady=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = BilgiYarismasi(root)
    root.mainloop() 