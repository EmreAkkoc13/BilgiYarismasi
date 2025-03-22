#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify # type: ignore
from flask_socketio import SocketIO, emit, join_room, leave_room # type: ignore
import sqlite3
import json
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli-anahtar-123'
socketio = SocketIO(app, cors_allowed_origins="*")

# Oda ve takım bilgilerini tutacak sözlükler
rooms = {}
sid_to_room = {}
sid_to_team = {}

# Aktif odaları tutacak sözlük
active_rooms = {}

class GameRoom:
    def __init__(self, room_code, host_name):
        self.room_code = room_code
        self.teams = [{"name": host_name, "is_host": True, "ready": False}]
        self.started = False
        self.current_question = 0
        self.questions = []
        self.scores = {host_name: 0}
        self.answers = {}

    def reset_answers(self):
        """Tüm takımların cevaplarını sıfırlar."""
        self.answers = {}

    def submit_answer(self, team_name, answer):
        """Takımın cevabını kaydeder ve doğruysa puan verir."""
        if team_name not in self.answers:
            self.answers[team_name] = answer
            
            # İlk kez cevap veriyorsa ve doğruysa puan ver
            if answer == self.questions[self.current_question]['correct_answer']:
                self.scores[team_name] = self.scores.get(team_name, 0) + 10
            
            return True
        return False

    def all_teams_answered(self):
        """Tüm takımlar cevap verdi mi kontrol eder."""
        return len(self.answers) == len(self.teams)

    def get_next_question(self):
        """Bir sonraki soruyu döndürür."""
        self.current_question += 1
        if self.current_question < len(self.questions):
            question = self.questions[self.current_question]
            return {
                'question': question['question'],
                'answer_a': question['options'][0],
                'answer_b': question['options'][1],
                'answer_c': question['options'][2],
                'answer_d': question['options'][3],
                'question_number': self.current_question + 1,
                'time': 30,
                'correct_answer': question['correct_answer']
            }
        return None

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    # Odadan çıkış işlemleri

@socketio.on('create_room')
def handle_create_room(data):
    team_name = data.get('team_name')
    room_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # Yeni oda oluştur
    active_rooms[room_code] = GameRoom(room_code, team_name)
    
    # Odaya katıl
    join_room(room_code)
    
    emit('room_created', {
        'room_code': room_code,
        'teams': active_rooms[room_code].teams
    })

@socketio.on('join_room')
def handle_join_room(data):
    """Odaya katılma isteğini işler."""
    room_code = data['room_code']
    team_name = data['team_name']
    print(f"Katılma isteği: {team_name} - Oda: {room_code}")
    
    if room_code in active_rooms:
        # Takımı odaya ekle
        active_rooms[room_code].teams.append({
            'name': team_name,
            'is_host': False,
            'ready': False
        })
        
        # Odaya katıl
        join_room(room_code)
        
        # Takım bilgilerini kaydet
        sid_to_room[request.sid] = room_code
        sid_to_team[request.sid] = team_name
        
        # Oda bilgilerini gönder
        emit('room_created', {
            'room_code': room_code,
            'teams': active_rooms[room_code].teams
        })
        
        # Tüm istemcilere güncel takım listesini gönder
        emit('teams_updated', {'teams': active_rooms[room_code].teams}, room=room_code)
    else:
        emit('error', {'message': 'Oda bulunamadı!'})

@socketio.on('toggle_ready')
def handle_toggle_ready(data):
    room_code = data.get('room_code')
    team_name = data.get('team_name')
    
    if room_code in active_rooms:
        room = active_rooms[room_code]
        for team in room.teams:
            if team['name'] == team_name and not team['is_host']:
                team['ready'] = not team['ready']
                break
        
        emit('room_updated', {
            'teams': room.teams
        }, room=room_code)

@socketio.on('start_game')
def handle_start_game(data):
    room_code = data.get('room_code')
    
    if room_code in active_rooms:
        room = active_rooms[room_code]
        
        # Tüm oyuncular hazır mı kontrol et
        if all(team['ready'] or team['is_host'] for team in room.teams):
            room.started = True
            # Soruları yükle
            conn = sqlite3.connect('quiz_data.db')
            cur = conn.cursor()
            cur.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 10")
            questions = []
            for row in cur.fetchall():
                questions.append({
                    'question': row[3],
                    'correct_answer': row[4],
                    'options': [row[5], row[6], row[7], row[8]]
                })
            conn.close()
            
            room.questions = questions
            # İlk soruyu hazırla
            first_question = {
                'question': questions[0]['question'],
                'answer_a': questions[0]['options'][0],
                'answer_b': questions[0]['options'][1],
                'answer_c': questions[0]['options'][2],
                'answer_d': questions[0]['options'][3],
                'question_number': 1,
                'time': 30,
                'correct_answer': questions[0]['correct_answer']
            }
            
            emit('game_started', {
                'first_question': first_question
            }, room=room_code)

@socketio.on('leave_room')
def handle_leave_room(data):
    room_code = data.get('room_code')
    team_name = data.get('team_name')
    
    if room_code in active_rooms:
        room = active_rooms[room_code]
        room.teams = [team for team in room.teams if team['name'] != team_name]
        leave_room(room_code)
        
        if not room.teams:
            # Oda boşsa sil
            del active_rooms[room_code]
        else:
            # Diğer oyunculara güncel listeyi gönder
            emit('room_updated', {
                'teams': room.teams
            }, room=room_code)

@socketio.on('chat_message')
def handle_chat_message(data):
    room_code = data.get('room_code')
    team_name = data.get('team_name')
    message = data.get('message')
    
    if room_code in active_rooms:
        emit('new_chat_message', {
            'team_name': team_name,
            'message': message
        }, room=room_code)

@socketio.on('next_question')
def handle_next_question():
    """Bir sonraki soruya geçer."""
    room_code = sid_to_room.get(request.sid)
    if room_code and room_code in active_rooms:
        room = active_rooms[room_code]
        # Tüm takımların cevaplarını sıfırla
        room.reset_answers()
        # Bir sonraki soruyu gönder
        next_question = room.get_next_question()
        if next_question:
            emit('show_question', next_question, room=room_code)
        else:
            # Oyun bitti
            emit('game_over', {'scores': room.scores}, room=room_code)

@socketio.on('time_up')
def handle_time_up(data):
    """Süre dolduğunda çalışır."""
    room_code = data.get('room_code')
    if room_code in active_rooms:
        room = active_rooms[room_code]
        
        # Doğru cevabı ve skorları göster
        correct_answer = room.questions[room.current_question]['correct_answer']
        
        # Tüm istemcilere sonuçları gönder
        emit('show_results', {
            'correct_answer': correct_answer,
            'scores': room.scores
        }, room=room_code)
        
        # 7 saniye bekle ve sonraki soruya geç
        socketio.sleep(7)
        
        # Sonraki soruya geç
        next_question = room.get_next_question()
        if next_question:
            emit('show_question', next_question, room=room_code)
        else:
            # Oyun bitti
            emit('game_over', {'scores': room.scores}, room=room_code)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Cevap gönderildiğinde çalışır."""
    room_code = data.get('room_code')
    team_name = data.get('team_name')
    answer = data.get('answer')
    
    if room_code in active_rooms:
        room = active_rooms[room_code]
        
        # Takımın cevabını kaydet
        if room.submit_answer(team_name, answer):
            # Tüm takımlar cevap verdi mi kontrol et
            if room.all_teams_answered():
                # Doğru cevabı ve skorları göster
                correct_answer = room.questions[room.current_question]['correct_answer']
                
                # Tüm istemcilere sonuçları gönder
                emit('show_results', {
                    'correct_answer': correct_answer,
                    'scores': room.scores
                }, room=room_code)
                
                # 7 saniye bekle ve sonraki soruya geç
                socketio.sleep(7)
                
                # Sonraki soruya geç
                next_question = room.get_next_question()
                if next_question:
                    emit('show_question', next_question, room=room_code)
                else:
                    # Oyun bitti
                    emit('game_over', {'scores': room.scores}, room=room_code)

if __name__ == '__main__':
    socketio.run(app, host='192.168.1.103', port=8080, debug=True) 
