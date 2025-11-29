import os
import json
import random
import time
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import re


# E-Waste Categories with Processing Data
EWASTE_CATEGORIES = {
    'battery': {
        'materials': ['lithium', 'cobalt', 'nickel', 'aluminum'],
        'processing_time': 15,
        'recovery_rate': 0.85,
        'hazard_level': 'high'
    },
    'cables': {
        'materials': ['copper', 'plastic', 'rubber'],
        'processing_time': 8,
        'recovery_rate': 0.92,
        'hazard_level': 'low'
    },
    'case': {
        'materials': ['steel', 'aluminum', 'plastic'],
        'processing_time': 12,
        'recovery_rate': 0.88,
        'hazard_level': 'low'
    },
    'cpu': {
        'materials': ['silicon', 'gold', 'silver', 'copper'],
        'processing_time': 25,
        'recovery_rate': 0.78,
        'hazard_level': 'medium'
    },
    'cpu_coolers': {
        'materials': ['aluminum', 'copper', 'steel'],
        'processing_time': 10,
        'recovery_rate': 0.90,
        'hazard_level': 'low'
    },
    'gpu': {
        'materials': ['silicon', 'gold', 'silver', 'copper', 'plastic'],
        'processing_time': 30,
        'recovery_rate': 0.75,
        'hazard_level': 'medium'
    },
    'hdd': {
        'materials': ['aluminum', 'steel', 'rare_earth_magnets'],
        'processing_time': 18,
        'recovery_rate': 0.82,
        'hazard_level': 'medium'
    },
    'headset': {
        'materials': ['plastic', 'copper', 'steel'],
        'processing_time': 6,
        'recovery_rate': 0.85,
        'hazard_level': 'low'
    },
    'keyboard': {
        'materials': ['plastic', 'rubber', 'copper'],
        'processing_time': 7,
        'recovery_rate': 0.88,
        'hazard_level': 'low'
    },
    'laptop': {
        'materials': ['aluminum', 'lithium', 'gold', 'silver', 'copper', 'plastic'],
        'processing_time': 45,
        'recovery_rate': 0.70,
        'hazard_level': 'high'
    },
    'microphone': {
        'materials': ['plastic', 'copper', 'steel'],
        'processing_time': 5,
        'recovery_rate': 0.87,
        'hazard_level': 'low'
    },
    'monitor': {
        'materials': ['glass', 'plastic', 'copper', 'lead'],
        'processing_time': 35,
        'recovery_rate': 0.73,
        'hazard_level': 'high'
    },
    'motherboard': {
        'materials': ['gold', 'silver', 'copper', 'palladium', 'silicon'],
        'processing_time': 40,
        'recovery_rate': 0.68,
        'hazard_level': 'high'
    },
    'mouse': {
        'materials': ['plastic', 'copper', 'steel'],
        'processing_time': 4,
        'recovery_rate': 0.90,
        'hazard_level': 'low'
    },
    'ram': {
        'materials': ['gold', 'silver', 'copper', 'silicon'],
        'processing_time': 20,
        'recovery_rate': 0.80,
        'hazard_level': 'medium'
    },
    'speakers': {
        'materials': ['plastic', 'copper', 'magnets'],
        'processing_time': 8,
        'recovery_rate': 0.85,
        'hazard_level': 'low'
    },
    'webcam': {
        'materials': ['plastic', 'copper', 'glass'],
        'processing_time': 6,
        'recovery_rate': 0.83,
        'hazard_level': 'low'
    }
}


class EWasteDigitalTwin:
    def __init__(self):
        self.processing_queue = []
        self.processed_items = []
        self.active_processes = {}
        self.total_materials_recovered = {}
        self.system_status = "idle"
        for cat in EWASTE_CATEGORIES.values():
            for mat in cat['materials']:
                self.total_materials_recovered[mat] = 0
        self.create_directory_structure()
       
    def create_directory_structure(self):
        """Create the exact directory structure for e-waste categories"""
        base_path = "data/e_waste"
        categories = list(EWASTE_CATEGORIES.keys())
       
        for category in categories:
            os.makedirs(f"{base_path}/{category}", exist_ok=True)
            self.create_sample_data(f"{base_path}/{category}", category)
   
    def create_sample_data(self, path, category):
        """Create sample data files for each category"""
        sample_data = {
            'category': category,
            'items_processed_today': random.randint(10, 100),
            'materials_recovered': EWASTE_CATEGORIES[category]['materials'],
            'efficiency': random.uniform(0.7, 0.95),
            'last_updated': datetime.now().isoformat()
        }
       
        with open(f"{path}/data.json", 'w') as f:
            json.dump(sample_data, f, indent=2)
   
    def add_to_queue(self, category, quantity=1):
        """Add items to processing queue"""
        for _ in range(quantity):
            item = {
                'id': f"{category}_{int(time.time())}_{random.randint(1000, 9999)}",
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'status': 'queued',
                'estimated_processing_time': EWASTE_CATEGORIES[category]['processing_time'],
                'progress': 0
            }
            self.processing_queue.append(item)
   
    def process_next_item(self):
        """Process the next item in the queue"""
        if not self.processing_queue:
            return None
           
        item = self.processing_queue.pop(0)
        item['status'] = 'processing'
        item['start_time'] = datetime.now().isoformat()
       
        self.active_processes[item['id']] = item
        self.system_status = "processing"
       
        threading.Thread(target=self.complete_processing, args=(item,)).start()
       
        return item
   
    def complete_processing(self, item):
        """Complete processing of an item"""
        category = item['category']
        processing_time = EWASTE_CATEGORIES[category]['processing_time']
       
        total_steps = 20
        for step in range(total_steps + 1):
            item['progress'] = (step / total_steps) * 100
            socketio.emit('system_stats', self.get_system_stats())
            time.sleep(min(processing_time / total_steps, 0.5))
       
        materials_recovered = {}
        for material in EWASTE_CATEGORIES[category]['materials']:
            base_amount = random.uniform(10, 100)
            if material in ['lithium', 'cobalt', 'nickel', 'lead', 'gold', 'silver', 'palladium']:
                base_amount = random.uniform(0.001, 0.05)
           
            recovery_rate = EWASTE_CATEGORIES[category]['recovery_rate']
            recovered = base_amount * recovery_rate * random.uniform(0.8, 1.2)
            materials_recovered[material] = round(recovered, 4)
           
            if material not in self.total_materials_recovered:
                self.total_materials_recovered[material] = 0
            self.total_materials_recovered[material] += recovered
       
        item['status'] = 'completed'
        item['end_time'] = datetime.now().isoformat()
        item['materials_recovered'] = materials_recovered
        item['recovery_efficiency'] = random.uniform(0.7, 0.95)
       
        self.processed_items.append(item)
        if item['id'] in self.active_processes:
            del self.active_processes[item['id']]
       
        if not self.active_processes and not self.processing_queue:
            self.system_status = "idle"
        elif self.processing_queue:
            self.system_status = "ready"
       
        socketio.emit('processing_complete', item)
   
    def get_system_stats(self):
        """Get current system statistics"""
        return {
            'queue_length': len(self.processing_queue),
            'active_processes': len(self.active_processes),
            'completed_today': len([item for item in self.processed_items
                                    if datetime.fromisoformat(item['timestamp']).date() == datetime.now().date()]),
            'total_processed': len(self.processed_items),
            'system_status': self.system_status,
            'total_materials_recovered': {k: round(v, 4) for k, v in self.total_materials_recovered.items()},
            'categories_breakdown': self.get_categories_breakdown(),
            'processing_queue': self.processing_queue,
            'active_items': list(self.active_processes.values()),
            'processed_items': self.processed_items
        }
   
    def get_categories_breakdown(self):
        """Get breakdown by category"""
        breakdown = {cat: {'count': 0, 'total_materials': {}} for cat in EWASTE_CATEGORIES}
        for item in self.processed_items:
            category = item['category']
            breakdown[category]['count'] += 1
           
            if 'materials_recovered' in item:
                for material, amount in item['materials_recovered'].items():
                    if material not in breakdown[category]['total_materials']:
                        breakdown[category]['total_materials'][material] = 0
                    breakdown[category]['total_materials'][material] += amount
        return breakdown


class Chatbot:
    """A simple rule-based chatbot for the dashboard."""
    def __init__(self, digital_twin):
        self.dt = digital_twin


    def get_response(self, user_message):
        user_message = user_message.lower().strip()
        stats = self.dt.get_system_stats()


        # Improved query matching
        if "hello" in user_message or "hi" in user_message:
            return "Hello! How can I assist you with the E-Waste Digital Twin today? 👋"


        if "help" in user_message or "commands" in user_message:
            return "I can answer questions about system status, the processing queue, active processes, and materials recovered. For example, try asking 'What's the queue length?' or 'How much gold have we recovered?'"


        if any(keyword in user_message for keyword in ["total processed", "items processed", "how many items"]):
            count = stats.get("total_processed", 0)
            return f"The system has processed a total of **{count}** items so far. 📊"


        if any(keyword in user_message for keyword in ["queue length", "queue status", "items in queue"]):
            length = stats.get("queue_length", 0)
            return f"There are currently **{length}** items waiting in the queue. 📋"


        if any(keyword in user_message for keyword in ["active processes", "processing now", "currently processing"]):
            active_count = stats.get("active_processes", 0)
            if active_count > 0:
                item_ids = list(self.dt.active_processes.keys())
                return f"There are **{active_count}** items being processed right now, including: {', '.join(item_ids)}. ⚙️"
            return "There are no items in active processing at the moment. 😴"


        if any(keyword in user_message for keyword in ["system status", "status of the system", "is the system"]):
            status = stats.get("system_status", "unknown").capitalize()
            return f"The current system status is **{status}**. ✨"
       
        # More robust material matching
        material_match = re.search(r'how much (\w+)|(\w+)\s+recovered', user_message)
        if material_match:
            material = material_match.group(1) or material_match.group(2)
            material = material.lower().replace(" ", "_")
            recovered_materials = stats.get("total_materials_recovered", {})
           
            # Check for close matches
            if material in recovered_materials:
                amount = recovered_materials[material]
                return f"We have recovered **{amount:.4f} kg** of {material.replace('_', ' ')} so far. 💎"
            else:
                return f"I don't have data for '{material.replace('_', ' ')}'. It might not be a primary material. 🤷"
       
        return "I'm sorry, I don't understand that request. Try asking about system status, queue, or materials. 🤖"


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Waste Digital Twin - Automated Deconstruction System</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }


        :root {
            --primary-dark: #0f0f23;
            --secondary-dark: #1a1a2e;
            --accent-blue: #16213e;
            --glass-bg: rgba(255, 255, 255, 0.08);
            --glass-border: rgba(255, 255, 255, 0.12);
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.8);
            --text-muted: rgba(255, 255, 255, 0.6);
            --success: #00d2aa;
            --warning: #ffb020;
            --error: #ff6b6b;
            --info: #4dabf7;
            --shadow-light: 0 8px 32px rgba(0, 0, 0, 0.1);
            --shadow-medium: 0 16px 64px rgba(0, 0, 0, 0.15);
            --shadow-heavy: 0 24px 96px rgba(0, 0, 0, 0.2);
            --border-radius: 16px;
            --border-radius-lg: 24px;
        }


        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, var(--primary-dark) 0%, var(--secondary-dark) 50%, var(--accent-blue) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            font-weight: 400;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }


        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 40px 20px;
        }


        .header {
            text-align: center;
            margin-bottom: 60px;
            position: relative;
        }


        .header::before {
            content: '';
            position: absolute;
            top: -20px;
            left: 50%;
            transform: translateX(-50%);
            width: 100px;
            height: 4px;
            background: linear-gradient(90deg, var(--success), var(--info));
            border-radius: 2px;
        }


        .header h1 {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 16px;
            background: linear-gradient(135deg, var(--text-primary), var(--text-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
        }


        .header p {
            font-size: 1.125rem;
            color: var(--text-secondary);
            font-weight: 400;
        }


        .system-status {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 50px;
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: var(--border-radius);
            padding: 24px 32px;
            box-shadow: var(--shadow-light);
        }


        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 16px;
            position: relative;
            animation: pulse 2s infinite;
        }


        .status-indicator::after {
            content: '';
            position: absolute;
            top: -4px;
            left: -4px;
            right: -4px;
            bottom: -4px;
            border-radius: 50%;
            background: inherit;
            opacity: 0.3;
            animation: ping 2s infinite;
        }


        .status-idle { background: var(--warning); }
        .status-processing { background: var(--success); }
        .status-error { background: var(--error); }
        .status-ready { background: var(--info); }


        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }


        @keyframes ping {
            75%, 100% {
                transform: scale(2);
                opacity: 0;
            }
        }


        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 24px;
            margin-bottom: 50px;
        }


        .card {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border-radius: var(--border-radius-lg);
            padding: 32px;
            border: 1px solid var(--glass-border);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }


        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
        }


        .card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: var(--shadow-heavy);
            border-color: rgba(255, 255, 255, 0.2);
        }


        .card h3 {
            margin-bottom: 24px;
            color: var(--text-primary);
            font-size: 1rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            opacity: 0.9;
        }


        .stat-value {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--success), var(--info));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
        }


        .stat-label {
            font-size: 0.875rem;
            color: var(--text-muted);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }


        .queue-section {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border-radius: var(--border-radius-lg);
            padding: 40px;
            margin-bottom: 32px;
            border: 1px solid var(--glass-border);
            box-shadow: var(--shadow-medium);
        }


        .queue-section h3 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 32px;
            color: var(--text-primary);
        }


        .add-item-form {
            display: grid;
            grid-template-columns: 2fr 1fr auto auto;
            gap: 20px;
            margin-bottom: 40px;
            align-items: end;
        }


        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }


        .form-group label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }


        select, input {
            padding: 16px 20px;
            border: 1px solid var(--glass-border);
            border-radius: var(--border-radius);
            font-size: 1rem;
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            color: var(--text-primary);
            transition: all 0.3s ease;
            font-family: inherit;
        }


        select:focus, input:focus {
            outline: none;
            border-color: var(--info);
            box-shadow: 0 0 0 3px rgba(77, 171, 247, 0.1);
        }


        select option {
            background: var(--secondary-dark);
            color: var(--text-primary);
        }


        button {
            padding: 16px 24px;
            border: none;
            border-radius: var(--border-radius);
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            font-family: inherit;
        }


        button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }


        button:active {
            transform: translateY(0);
        }


        button:not(.process-btn) {
            background: linear-gradient(135deg, var(--success), #00a085);
            color: white;
        }


        .process-btn {
            background: linear-gradient(135deg, var(--info), #3b82f6);
            color: white;
        }


        .queue-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 32px;
        }


        .queue-section-title {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 12px;
        }


        .queue-items {
            max-height: 320px;
            overflow-y: auto;
            margin-bottom: 15px;
            border-radius: var(--border-radius);
            padding: 4px;
        }


        .queue-items::-webkit-scrollbar {
            width: 6px;
        }


        .queue-items::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 3px;
        }


        .queue-items::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }


        .queue-item, .process-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 16px 20px;
            margin-bottom: 12px;
            border-radius: var(--border-radius);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s ease;
        }


        .queue-item:hover, .process-item:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateX(4px);
        }


        .materials-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-top: 24px;
        }


        .material-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 24px 20px;
            border-radius: var(--border-radius);
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s ease;
        }


        .material-card:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-4px);
            box-shadow: var(--shadow-light);
        }


        .material-amount {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--success);
            margin-bottom: 8px;
        }


        .material-name {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }


        .category-breakdown {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-top: 32px;
        }


        .category-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 24px;
            border-radius: var(--border-radius);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s ease;
        }


        .category-item:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
        }


        .category-name {
            font-weight: 600;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.875rem;
        }


        .progress-bar {
            background: rgba(255, 255, 255, 0.1);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin: 16px 0;
        }


        .progress-fill {
            background: linear-gradient(90deg, var(--success), var(--info));
            height: 100%;
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 4px;
        }


        .chart-container {
            position: relative;
            height: 350px;
            margin-top: 32px;
        }


        .realtime-log {
            background: rgba(0, 0, 0, 0.4);
            padding: 24px;
            border-radius: var(--border-radius);
            height: 280px;
            overflow-y: auto;
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
            font-size: 0.875rem;
            line-height: 1.6;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }


        .realtime-log::-webkit-scrollbar {
            width: 6px;
        }


        .realtime-log::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 3px;
        }


        .realtime-log::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }


        .log-entry {
            margin-bottom: 8px;
            padding: 4px 0;
            border-left: 2px solid transparent;
            padding-left: 12px;
            transition: all 0.3s ease;
        }


        .log-entry:hover {
            background: rgba(255, 255, 255, 0.05);
            border-left-color: var(--info);
        }


        .log-timestamp { color: var(--info); font-weight: 500; }
        .log-success { border-left-color: var(--success); }
        .log-info { border-left-color: var(--warning); }
        .log-error { border-left-color: var(--error); }


        @media (max-width: 1024px) {
            .add-item-form {
                grid-template-columns: 1fr 1fr;
                gap: 16px;
            }
           
            .queue-content {
                grid-template-columns: 1fr;
                gap: 24px;
            }
        }


        @media (max-width: 768px) {
            .container { padding: 20px 16px; }
            .dashboard-grid { grid-template-columns: 1fr; }
            .add-item-form { grid-template-columns: 1fr; }
            .header h1 { font-size: 2.5rem; }
            .card { padding: 24px; }
            .queue-section { padding: 24px; }
            .stat-value { font-size: 2.5rem; }
        }


        /* Enhanced animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }


        .card {
            animation: fadeInUp 0.6s ease-out;
        }


        .card:nth-child(2) { animation-delay: 0.1s; }
        .card:nth-child(3) { animation-delay: 0.2s; }
        .card:nth-child(4) { animation-delay: 0.3s; }


        /* Empty state styling */
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-muted);
            font-style: italic;
        }


        /* Chatbot UI */
        .chat-button {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            background: linear-gradient(45deg, var(--info), #3b82f6);
            border-radius: 50%;
            border: none;
            box-shadow: 0 4px 15px rgba(77, 170, 247, 0.4);
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            z-index: 2000;
        }
       
        .chat-button:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(77, 170, 247, 0.6);
        }
       
        .chat-button img {
            width: 32px;
            height: 32px;
            filter: invert(1);
        }


        .chat-container {
            position: fixed;
            bottom: 100px;
            right: 30px;
            width: 350px;
            height: 500px;
            background: rgba(18, 18, 38, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: var(--border-radius);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            display: none;
            flex-direction: column;
            overflow: hidden;
            z-index: 1000;
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.3s ease, transform 0.3s ease;
        }


        .chat-container.active {
            display: flex;
            opacity: 1;
            transform: translateY(0);
        }


        .chat-header {
            background: var(--glass-bg);
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            border-bottom: 1px solid var(--glass-border);
        }
       
        .chat-messages {
            flex-grow: 1;
            padding: 1rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }


        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }
        .chat-messages::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 3px;
        }
        .chat-messages::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }


        .chat-message {
            padding: 0.8rem 1.2rem;
            border-radius: 1rem;
            margin-bottom: 1rem;
            max-width: 80%;
            font-size: 0.9rem;
        }
       
        .chat-message.user {
            background: linear-gradient(45deg, #3b82f6, #4daaf7);
            align-self: flex-end;
            text-align: right;
            border-bottom-right-radius: 0.2rem;
        }
       
        .chat-message.bot {
            background: rgba(255, 255, 255, 0.07);
            border-left: 3px solid var(--success);
            align-self: flex-start;
            border-bottom-left-radius: 0.2rem;
        }
       
        .chat-input-container {
            padding: 1rem;
            border-top: 1px solid var(--glass-border);
            display: flex;
            gap: 0.75rem;
        }
       
        .chat-input {
            flex-grow: 1;
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            padding: 0.75rem;
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-primary);
            font-size: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>E-Waste Digital Twin</h1>
            <p>Automated Deconstruction System • Real-time Monitoring Dashboard</p>
        </div>


        <div class="system-status">
            <div class="status-indicator status-idle" id="statusIndicator"></div>
            <span id="systemStatus" style="font-weight: 600; font-size: 1.125rem;">System Idle</span>
        </div>


        <div class="dashboard-grid">
            <div class="card">
                <h3>📊 System Overview</h3>
                <div class="stat-value" id="totalProcessed">0</div>
                <div class="stat-label">Total Items Processed</div>
            </div>
            <div class="card">
                <h3>⏳ Queue Status</h3>
                <div class="stat-value" id="queueLength">0</div>
                <div class="stat-label">Items in Queue</div>
            </div>
            <div class="card">
                <h3>⚡ Active Processes</h3>
                <div class="stat-value" id="activeProcesses">0</div>
                <div class="stat-label">Currently Processing</div>
            </div>
            <div class="card">
                <h3>📈 Today's Progress</h3>
                <div class="stat-value" id="completedToday">0</div>
                <div class="stat-label">Completed Today</div>
            </div>
        </div>


        <div class="queue-section">
            <h3>Processing Control Center</h3>
            <div class="add-item-form">
                <div class="form-group">
                    <label>E-Waste Category</label>
                    <select id="categorySelect">
                        <option value="">Select Category...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Quantity</label>
                    <input type="number" id="quantityInput" value="1" min="1" max="50">
                </div>
                <div class="form-group">
                    <button onclick="addToQueue()">Add to Queue</button>
                </div>
                <div class="form-group">
                    <button class="process-btn" onclick="startProcessing()">Start Processing</button>
                </div>
            </div>


            <div class="queue-content">
                <div>
                    <div class="queue-section-title">
                        <span>📋</span>Processing Queue
                    </div>
                    <div class="queue-items" id="queueItems">
                        <div class="empty-state">Queue is empty</div>
                    </div>
                </div>
                <div>
                    <div class="queue-section-title">
                        <span>⚙️</span>Active Processing
                    </div>
                    <div class="queue-items" id="activeItems">
                        <div class="empty-state">No active processes</div>
                    </div>
                </div>
            </div>
        </div>


        <div class="card">
            <h3>💎 Materials Recovery Summary</h3>
            <div class="materials-grid" id="materialsGrid">
                <div class="empty-state">No materials recovered yet</div>
            </div>
        </div>


        <div class="card">
            <h3>📊 Processing Analytics</h3>
            <div class="chart-container">
                <canvas id="processingChart"></canvas>
            </div>
        </div>


        <div class="card">
            <h3>🏭 Category Breakdown</h3>
            <div class="category-breakdown" id="categoryBreakdown">
                <div class="empty-state">Processing data will appear here</div>
            </div>
        </div>


        <div class="card">
            <h3>📝 Real-time Activity Log</h3>
            <div class="realtime-log" id="activityLog">
                <div class="log-entry log-info">
                    <span class="log-timestamp">[System]</span>
                    <span> Digital Twin System Initialized</span>
                </div>
            </div>
        </div>
    </div>


    <button class="chat-button" onclick="toggleChatbot()">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-message-circle">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-4.2A8.38 8.38 0 0 1 3 11.5a8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
        </svg>
    </button>
   
    <div class="chat-container" id="chatbotContainer">
        <div class="chat-header">
            <span>AI Assistant</span>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="chat-message bot">
                Hello! I'm your E-Waste Digital Twin Assistant. I can help you with real-time stats, queue information, and materials recovery.
            </div>
        </div>
        <div class="chat-input-container">
            <input type="text" class="chat-input" id="chatInput" placeholder="Ask me anything..." onkeypress="handleChatKeyPress(event)">
            <button onclick="sendChatMessage()">Send</button>
        </div>
    </div>


    <script>
        const socket = io();
        let processingChart;
        let lastStats = {};


        document.addEventListener('DOMContentLoaded', function() {
            loadCategories();
            initializeChart();
            fetchSystemStats();
        });


        socket.on('connect', function() { addLog('Connected to Digital Twin System', 'success'); });
        socket.on('system_stats', function(data) { updateSystemStats(data); });
        socket.on('processing_started', function(item) { addLog(`Started processing ${item.category} item: ${item.id}`, 'info'); updateActiveItems(); });
        socket.on('processing_complete', function(item) { addLog(`Completed processing ${item.category} item: ${item.id}`, 'success'); fetchSystemStats(); });
        socket.on('queue_updated', function(data) { updateSystemStats(data); });


        async function loadCategories() {
            try {
                const response = await fetch(window.location.origin + '/api/categories');
                const categories = await response.json();
                const select = document.getElementById('categorySelect');
                Object.keys(categories).forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category.replace('_', ' ').toUpperCase();
                    select.appendChild(option);
                });
            } catch (error) { addLog('Error loading categories: ' + error.message, 'error'); }
        }


        function addToQueue() {
            const category = document.getElementById('categorySelect').value;
            const quantity = parseInt(document.getElementById('quantityInput').value);
            if (!category) { alert('Please select a category'); return; }
            socket.emit('add_to_queue', { category: category, quantity: quantity });
            addLog(`Added ${quantity} ${category} item(s) to queue`, 'info');
        }


        function startProcessing() { socket.emit('start_processing'); }


        async function fetchSystemStats() {
            try {
                const response = await fetch(window.location.origin + '/api/stats');
                const data = await response.json();
                updateSystemStats(data);
            } catch (error) { addLog('Error fetching system stats: ' + error.message, 'error'); }
        }


        function updateSystemStats(data) {
            if (!data) return;
            document.getElementById('totalProcessed').textContent = data.total_processed || 0;
            document.getElementById('queueLength').textContent = data.queue_length || 0;
            document.getElementById('activeProcesses').textContent = data.active_processes || 0;
            document.getElementById('completedToday').textContent = data.completed_today || 0;


            const statusIndicator = document.getElementById('statusIndicator');
            const systemStatus = document.getElementById('systemStatus');
            statusIndicator.className = `status-indicator status-${data.system_status}`;
            systemStatus.textContent = `System ${data.system_status.charAt(0).toUpperCase() + data.system_status.slice(1)}`;


            updateMaterialsDisplay(data.total_materials_recovered || {});
            updateCategoryBreakdown(data.categories_breakdown || {});
            updateChart(data.categories_breakdown || {});
           
            updateQueueDisplay(data.processing_queue);
            updateActiveItems(data.active_items || {});
        }


        function updateMaterialsDisplay(materials) {
            const container = document.getElementById('materialsGrid');
            if (Object.keys(materials).length === 0) {
                container.innerHTML = '<div class="empty-state">No materials recovered yet</div>';
                return;
            }
            container.innerHTML = '';
            Object.entries(materials).forEach(([material, amount]) => {
                const card = document.createElement('div');
                card.className = 'material-card';
                card.innerHTML = `
                    <div class="material-amount">${amount.toFixed(2)} kg</div>
                    <div class="material-name">${material.replace('_', ' ')}</div>
                `;
                container.appendChild(card);
            });
        }


        function updateCategoryBreakdown(categories) {
            const container = document.getElementById('categoryBreakdown');
            if (Object.keys(categories).length === 0) {
                container.innerHTML = '<div class="empty-state">Processing data will appear here</div>';
                return;
            }
            container.innerHTML = '';
            Object.entries(categories).forEach(([category, stats]) => {
                const item = document.createElement('div');
                item.className = 'category-item';
                const percentage = (stats.count / (lastStats.total_processed || 1)) * 100 || 0;
                item.innerHTML = `
                    <div class="category-name">${category.replace('_', ' ')}</div>
                    <div style="color: var(--text-secondary); margin-bottom: 8px;">${stats.count || 0} items processed</div>
                    <div class="progress-bar"><div class="progress-fill" style="width:${percentage}%"></div></div>
                `;
                container.appendChild(item);
            });
        }


        function initializeChart() {
            const ctx = document.getElementById('processingChart').getContext('2d');
            processingChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Items Processed',
                        data: [],
                        backgroundColor: 'rgba(0, 210, 170, 0.8)',
                        borderColor: '#00d2aa',
                        borderWidth: 2,
                        borderRadius: 8,
                        borderSkipped: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: 'rgba(255, 255, 255, 0.8)',
                                font: { family: 'Inter', weight: 500 }
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: 'rgba(255, 255, 255, 0.6)' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: { color: 'rgba(255, 255, 255, 0.6)' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    }
                }
            });
        }


        function updateChart(categories) {
            if (!processingChart) return;
            processingChart.data.labels = Object.keys(categories).map(c => c.replace('_', ' ').toUpperCase());
            processingChart.data.datasets[0].data = Object.values(categories).map(c => c.count || 0);
            processingChart.update();
        }


        function updateQueueDisplay(queueItems) {
            const container = document.getElementById('queueItems');
            if (queueItems.length === 0) {
                container.innerHTML = '<div class="empty-state">Queue is empty</div>';
                return;
            }
            container.innerHTML = '';
            queueItems.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'queue-item';
                itemDiv.innerHTML = `
                    <div style="font-weight: bold;">${item.id}</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary);">${item.category.replace('_', ' ').toUpperCase()}</div>
                `;
                container.appendChild(itemDiv);
            });
        }


        function updateActiveItems(activeItems) {
            const activeContainer = document.getElementById('activeItems');
            if (activeItems.length === 0) {
                activeContainer.innerHTML = '<div class="empty-state">No active processes</div>';
                return;
            }
            activeContainer.innerHTML = '';
            activeItems.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'process-item';
                itemDiv.innerHTML = `
                    <div style="font-weight: bold;">${item.id}</div>
                    <div style="flex-grow: 1; margin: 0 1rem;">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${item.progress || 0}%"></div>
                        </div>
                    </div>
                `;
                activeContainer.appendChild(itemDiv);
            });
        }
       
        function addLog(message, type='info') {
            const log = document.getElementById('activityLog');
            const entry = document.createElement('div');
            entry.className = `log-entry log-${type}`;
            entry.innerHTML = `<span class="log-timestamp">[${new Date().toLocaleTimeString()}]</span> <span>${message}</span>`;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
        }


        // Chatbot functions
        function toggleChatbot() {
            const chatContainer = document.getElementById('chatbotContainer');
            chatContainer.classList.toggle('active');
        }


        function handleChatKeyPress(event) {
            if (event.key === 'Enter') {
                sendChatMessage();
            }
        }


        async function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!message) return;


            addChatMessage(message, 'user');
            input.value = '';


            try {
                const response = await fetch(window.location.origin + '/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });


                if (response.ok) {
                    const data = await response.json();
                    addChatMessage(data.response, 'bot');
                } else {
                    addChatMessage("Sorry, I'm having trouble connecting to the system.", 'bot');
                }
            } catch (error) {
                console.error('Chatbot error:', error);
                addChatMessage("An error occurred. Please try again later.", 'bot');
            }
        }


        function addChatMessage(message, sender) {
            const container = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${sender}`;
            messageDiv.innerHTML = message;
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
    </script>
</body>
</html>
"""


# App initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ewaste_digital_twin_2024'
socketio = SocketIO(app, cors_allowed_origins="*")


# Initialize the digital twin and chatbot
digital_twin = EWasteDigitalTwin()
chatbot = Chatbot(digital_twin)


# Flask Routes
@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/stats')
def api_stats():
    return jsonify(digital_twin.get_system_stats())


@app.route('/api/queue', methods=['GET', 'POST'])
def api_queue():
    if request.method == 'POST':
        data = request.json
        category = data.get('category')
        quantity = data.get('quantity', 1)
        if category in EWASTE_CATEGORIES:
            digital_twin.add_to_queue(category, quantity)
            socketio.emit('system_stats', digital_twin.get_system_stats())
            return jsonify({'success': True, 'message': f'Added {quantity} {category} items to queue'})
        return jsonify({'success': False, 'message': 'Invalid category'})
    return jsonify({
        'queue': digital_twin.processing_queue,
        'active_processes': list(digital_twin.active_processes.values())
    })


@app.route('/api/process')
def api_process():
    item = digital_twin.process_next_item()
    if item:
        socketio.emit('processing_started', item, broadcast=True)
        return jsonify({'success': True, 'item': item})
    return jsonify({'success': False, 'message': 'No items in queue'})


@app.route('/api/categories')
def api_categories():
    return jsonify(EWASTE_CATEGORIES)


@app.route('/api/processed')
def api_processed():
    return jsonify(digital_twin.processed_items[-50:])


@app.route('/api/chat', methods=['POST'])
def api_chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    bot_response = chatbot.get_response(user_message)
    return jsonify({'response': bot_response})


# WebSocket Events
@socketio.on('connect')
def handle_connect():
    emit('system_stats', digital_twin.get_system_stats())


@socketio.on('start_processing')
def handle_start_processing():
    item = digital_twin.process_next_item()
    if item:
        emit('processing_started', item, broadcast=True)


@socketio.on('add_to_queue')
def handle_add_to_queue(data):
    category = data['category']
    quantity = data.get('quantity', 1)
    digital_twin.add_to_queue(category, quantity)
    emit('queue_updated', digital_twin.get_system_stats(), broadcast=True)


# Auto-processing simulation
def auto_process():
    while True:
        time.sleep(10)
        if digital_twin.processing_queue and len(digital_twin.active_processes) < 3:
            digital_twin.process_next_item()
        socketio.emit('system_stats', digital_twin.get_system_stats())


threading.Thread(target=auto_process, daemon=True).start()


if __name__ == '__main__':
    for category in list(EWASTE_CATEGORIES.keys())[:5]:
        digital_twin.add_to_queue(category, random.randint(1, 3))
   
    socketio.run(app, debug=True, host='0.0.0.0', port=5003)

