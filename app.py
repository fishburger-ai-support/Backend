import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
from gigachat_client import GigaChatClient
from email_handler import EmailHandler
from notifications import TelegramNotifier
from models import db, Ticket

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'dev-key')

db.init_app(app)

# Инициализация сервисов
gigachat = GigaChatClient()
email_handler = EmailHandler()
telegram = TelegramNotifier()

# ==================== API ЭНДПОИНТЫ ====================

@app.route('/api/webhook/email', methods=['POST'])
def handle_email():
    """Приём письма от почтового сервера"""
    try:
        data = request.json
        email_from = data.get('from', '')
        subject = data.get('subject', '')
        body = data.get('body', '')
        
        print(f"📧 Получено письмо от {email_from}")
        
        # Анализ через GigaChat
        analysis = gigachat.analyze_email(body, subject, email_from)
        if not analysis:
            return jsonify({'error': 'AI не смог обработать письмо'}), 500
        
        # Создание тикета
        ticket = Ticket(
            date=datetime.now(),
            full_name=analysis.get('full_name'),
            object_name=analysis.get('object_name'),
            phone=analysis.get('phone'),
            email=email_from,
            serial_numbers=analysis.get('serial_numbers'),
            device_type=analysis.get('device_type'),
            sentiment=analysis.get('sentiment', 'нейтрально'),
            issue_summary=analysis.get('issue_summary'),
            original_message=body,
            ai_draft=analysis.get('draft_reply'),
            status=analysis.get('decision', 'new'),
            context={'subject': subject}
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        # Обработка решения AI
        if analysis.get('decision') == 'full_answer':
            email_handler.send_email(
                to=email_from,
                subject=f"Re: {subject}",
                body=analysis['draft_reply']
            )
            ticket.status = 'answered'
            ticket.final_answer = analysis['draft_reply']
            
        elif analysis.get('decision') == 'need_more_info':
            email_handler.send_email(
                to=email_from,
                subject="Уточнение по обращению",
                body=analysis['draft_reply']
            )
            ticket.status = 'need_info'
            
        elif analysis.get('decision') == 'escalate_to_human':
            telegram.send_notification(
                f"⚠️ Новое обращение #{ticket.id} требует внимания!\n"
                f"От: {ticket.full_name}\n{ticket.issue_summary}"
            )
            ticket.status = 'human_needed'
        
        db.session.commit()
        
        return jsonify({'status': 'ok', 'ticket_id': ticket.id})
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tickets/table', methods=['GET'])
def get_tickets_table():
    """Данные для отображения в таблице (только 9 полей)"""
    tickets = Ticket.query.order_by(Ticket.date.desc()).all()
    return jsonify([ticket.for_table() for ticket in tickets])


@app.route('/api/tickets', methods=['GET'])
def get_all_tickets():
    """Все данные тикетов (со служебными полями)"""
    tickets = Ticket.query.order_by(Ticket.date.desc()).all()
    return jsonify([ticket.to_dict() for ticket in tickets])


@app.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Детали конкретного тикета"""
    ticket = Ticket.query.get_or_404(ticket_id)
    return jsonify(ticket.to_dict())


@app.route('/api/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    """Обновление тикета оператором"""
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.json
    
    editable_fields = [
        'full_name', 'object_name', 'phone', 'serial_numbers',
        'device_type', 'sentiment', 'issue_summary', 'final_answer', 'status'
    ]
    
    for field in editable_fields:
        if field in data:
            setattr(ticket, field, data[field])
    
    ticket.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify(ticket.to_dict())


@app.route('/api/tickets/<int:ticket_id>/reply', methods=['POST'])
def send_reply(ticket_id):
    """Отправка ответа оператором"""
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.json
    
    reply_text = data.get('reply_text', ticket.final_answer or ticket.ai_draft)
    
    email_handler.send_email(
        to=ticket.email,
        subject=f"Re: {ticket.context.get('subject', 'Поддержка')}",
        body=reply_text
    )
    
    ticket.final_answer = reply_text
    ticket.status = 'answered'
    ticket.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify({'status': 'ok'})


@app.route('/api/tickets/export/csv', methods=['GET'])
def export_csv():
    """Экспорт таблицы в CSV"""
    import csv
    from io import StringIO
    from flask import Response
    
    tickets = Ticket.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        'ID', 'Дата', 'ФИО', 'Объект', 'Телефон', 'Email',
        'Заводские номера', 'Тип приборов', 'Тональность', 'Суть вопроса', 'Статус'
    ])
    
    # Данные
    for t in tickets:
        writer.writerow([
            t.id, t.date, t.full_name, t.object_name, t.phone, t.email,
            t.serial_numbers, t.device_type, t.sentiment, t.issue_summary, t.status
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=tickets.csv'}
    )


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Статистика для дашборда"""
    from sqlalchemy import func
    from datetime import timedelta
    
    # По статусам
    status_stats = db.session.query(
        Ticket.status, func.count(Ticket.status)
    ).group_by(Ticket.status).all()
    
    # По тональности
    sentiment_stats = db.session.query(
        Ticket.sentiment, func.count(Ticket.sentiment)
    ).group_by(Ticket.sentiment).all()
    
    # За последние 7 дней
    week_ago = datetime.now() - timedelta(days=7)
    daily_stats = db.session.query(
        func.date(Ticket.date), func.count(Ticket.id)
    ).filter(Ticket.date >= week_ago).group_by(
        func.date(Ticket.date)
    ).all()
    
    return jsonify({
        'by_status': dict(status_stats),
        'by_sentiment': dict(sentiment_stats),
        'daily': [{'date': str(d), 'count': c} for d, c in daily_stats]
    })


@app.route('/')
def index():
    """Главная страница с таблицей"""
    return render_template('index.html')


@app.route('/health', methods=['GET'])
def health():
    """Проверка работоспособности"""
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('DEBUG') == 'True')