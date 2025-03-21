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
        self.scores = {}

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
            emit('game_started', {
                'first_question': questions[0]
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

if __name__ == '__main__':
    socketio.run(app, host='192.168.1.102', port=8080, debug=True) 
