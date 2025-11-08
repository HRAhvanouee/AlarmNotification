import tkinter as tk 
from tkinter import ttk
import paho.mqtt.client as mqtt
import json
from datetime import datetime

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "aas/alarm/notifications"

# ----------------- Data Processing -----------------
def extract_alarm_info(data):
    alarm_info = {
        "ActivationTime": "N/A",
        "OperatorAcknowledgment": "N/A",
        "AcknowledgmentTime": "N/A",
        "DeactivationTime": "N/A",
        "AlarmFloodClassLabel": "N/A",
        "AlarmConfiguration": "N/A"
    }

    if "value" in data and isinstance(data["value"], list):
        for item in data["value"]:
            key = item.get("idShort", "")
            if key in alarm_info:
                if key == "AlarmConfiguration":
                    try:
                        alarm_info[key] = item["value"]["keys"][0]["value"]
                    except Exception:
                        alarm_info[key] = "N/A"
                else:
                    alarm_info[key] = item.get("value", "N/A")
    return alarm_info

# ----------------- MQTT Callbacks -----------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        status_label.config(text="🟢 Connected", foreground="#44ff44")
        client.subscribe(TOPIC)
    else:
        status_label.config(text=f"🔴 Connection failed ({rc})", foreground="#ff4444")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        alarm_info = extract_alarm_info(data)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Determine color tag based on AlarmFloodClassLabel
        flood_class = alarm_info["AlarmFloodClassLabel"].lower()
        if "low" in flood_class:
            tag = "low"
        elif "high" in flood_class:
            tag = "high"
        elif "normal" in flood_class:
            tag = "normal"
        else:
            tag = ""

        # Insert into table with color tag
        tree.insert(
            "",
            "end",
            values=(
                alarm_info["ActivationTime"],
                alarm_info["OperatorAcknowledgment"],
                alarm_info["AcknowledgmentTime"],
                alarm_info["DeactivationTime"],
                alarm_info["AlarmFloodClassLabel"],
                alarm_info["AlarmConfiguration"]
            ),
            tags=(tag,)
        )

        footer_label.config(text=f"Last update: {timestamp}")
        last_notif_label.config(
            text=f"Last Notification ➜ {alarm_info['AlarmConfiguration']} | Flood Class: {alarm_info['AlarmFloodClassLabel']} | Time: {alarm_info['ActivationTime']}"
        )

    except Exception as e:
        print("⚠️ Error processing message:", e)

# ----------------- GUI Setup -----------------
root = tk.Tk()
root.title("⚠️ Alarm Notification Dashboard")
root.geometry("1200x650")
root.configure(bg="#1e1e1e")

# Apply ttk theme style
style = ttk.Style()
style.theme_use("clam")

style.configure("Treeview",
                background="#2b2b2b",
                foreground="white",
                rowheight=28,
                fieldbackground="#2b2b2b",
                font=("Segoe UI", 10))
style.configure("Treeview.Heading",
                background="#3c3f41",
                foreground="white",
                font=("Segoe UI Semibold", 11))
style.map("Treeview", background=[("selected", "#0078d7")])

# ----------------- Header -----------------
header_frame = tk.Frame(root, bg="#292929", height=70)
header_frame.pack(fill="x")

title_label = tk.Label(header_frame, text="Alarm Notification HMI",
                       font=("Segoe UI Semibold", 18), fg="white", bg="#292929")
title_label.pack(side="left", padx=20, pady=10)

status_label = tk.Label(header_frame, text="🔴 Disconnected",
                        font=("Segoe UI", 12), fg="#ff4444", bg="#292929")
status_label.pack(side="right", padx=20)


# ----------------- Table -----------------
table_frame = tk.Frame(root, bg="#1e1e1e")
table_frame.pack(fill="both", expand=True, padx=15, pady=15)

columns = (
    "ActivationTime",
    "OperatorAcknowledgment",
    "AcknowledgmentTime",
    "DeactivationTime",
    "AlarmFloodClassLabel",
    "AlarmConfiguration"
)

tree = ttk.Treeview(table_frame, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col, anchor="center")
    tree.column(col, anchor="center", width=180, minwidth=100)

tree.tag_configure("low", foreground="yellow")
tree.tag_configure("normal", foreground="orange")
tree.tag_configure("high", foreground="red")

scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
tree.configure(yscroll=scroll_y.set, xscroll=scroll_x.set)

tree.grid(row=0, column=0, sticky="nsew")
scroll_y.grid(row=0, column=1, sticky="ns")
scroll_x.grid(row=1, column=0, sticky="ew")

table_frame.grid_rowconfigure(0, weight=1)
table_frame.grid_columnconfigure(0, weight=1)

# ----------------- Footer -----------------
footer_label = tk.Label(root, text="Waiting for messages...",
                        font=("Segoe UI", 10), fg="#bbbbbb", bg="#1e1e1e", anchor="w")
footer_label.pack(fill="x", padx=15, pady=(0, 5))

last_notif_label = tk.Label(root, text="Last Notification ➜ None",
                            font=("Segoe UI Semibold", 10), fg="#88c0ff", bg="#1e1e1e", anchor="w")
last_notif_label.pack(fill="x", padx=15, pady=(0, 10))


# ----------------- MQTT Setup -----------------
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

# ----------------- Run -----------------
root.mainloop()
