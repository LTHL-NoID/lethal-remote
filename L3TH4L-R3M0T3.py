import os
import socket
import ctypes
import datetime
import threading
import subprocess
import PySimpleGUI as sg
from pynput.keyboard import Listener as KeyboardListener, Key
from pynput.mouse import Listener as MouseListener, Button

# vars
PORT = 13376
target_ip = ''
listener = None
update_state = False
save_dir = (r'C:\ProgramData\L3TH4L-R3M0T3')
config = (r'C:\ProgramData\L3TH4L-R3M0T3\L3TH4L-R3M0T3.cfg')
log = (r'C:\ProgramData\L3TH4L-R3M0T3\L3TH4L-error.log')
icon_path = (r'C:\ProgramData\L3TH4L-R3M0T3\appIcon.ico')
normal = (r'C:\ProgramData\L3TH4L-R3M0T3\normal.png')
muted = (r'C:\ProgramData\L3TH4L-R3M0T3\muted.png')
unmuted = (r'C:\ProgramData\L3TH4L-R3M0T3\unmuted.png')

key_binding = None
bind_event = threading.Event()

# Save log error
def error_log(info):
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
    with open(log, 'w') as file:
        file.write(f"{timestamp} - {str(info)}\n")

def check_config():
    if os.path.exists(config):
        with open(config, 'r') as file:
            target_ip = file.readline().strip()
            key_binding = file.readline().strip()
            return target_ip, key_binding
    else:
        target_ip = resolve_address()
        key_binding = None
        return target_ip, key_binding

def save_config(ip, key_binding):
    if key_binding is None:
        key_binding = 'Not Set'
    with open(config, 'w') as f:
        f.write(f"{ip}\n{key_binding}\n")
    #print(f"Configuration saved: Address: {ip}, Key:{key_binding}")

def resolve_address():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as host:
            host.connect(('1.1.1.1', 1))
            return host.getsockname()[0]
    except Exception as e:
        error_log('Unable to resolve host: ' + str(e))

def on_disconnect():
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.015)
            s.connect((target_ip, PORT))
            s.sendall(b'Disconnected @'+ timestamp.encode())
            if listener:
                listener.stop()
    except Exception:
        error_log('Unable to resolve host: on_disconnect')

def validate_ip(target_ip, local_ip):
    target_octets = target_ip.split('.')
    local_octets = local_ip.split('.')
    if len(target_octets) != 4:
        window['-OUTPUT-'].update('Invalid IP address!')
        return False
    elif target_octets[-1] in ['0', '1', '255']:
        window['-OUTPUT-'].update('0, 1 & 255 cannot be used.')
        return False
    elif target_octets[:3] != local_octets[:3]:
        window['-OUTPUT-'].update("First 3 octets don't match!")
        return False
    elif any(not (char.isdigit() or char == '.') for octet in target_octets for char in octet):
        window['-OUTPUT-'].update("Invalid characters in IP address!")
        return False
    else:
        try:
            result = subprocess.run(['ping', '-n', '1', '-w', '250', target_ip],
                                    capture_output=True,
                                    text=True,
                                    check=True,
                                    shell=True)
            online = 'Reply from' in result.stdout
            if online:
                window['-OUTPUT-'].update(f'Target {target_ip} is Online!')
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.015)
                    s.connect((target_ip, PORT))
                    s.sendall(b'Connected!')
            except Exception:
                error_log('Unable to resolve host during validate_ip')
                window['-OUTPUT-'].update('Target is offline ¯\\_(ツ)_/¯')
            return online
        except subprocess.CalledProcessError:
            window['-OUTPUT-'].update('Target is offline ¯\\_(ツ)_/¯')

def is_port_open(ip, PORT):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.015)
            s.connect((ip, PORT))
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def toggle_state():
    global update_state, target_ip
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.015)
            s.connect((target_ip, PORT))
            update_state = not update_state
            status = 'Muted' if update_state else 'Unmuted'
            window['-OUTPUT-'].update(f'{status} Mic.')
            window.write_event_value('UPDATE_IMAGE', status.lower())
            s.sendall(f'{status}.'.encode())
    except Exception as e:
        error_log(f"toggle_state failed: {e}")

def on_key_press(key):
    global key_binding
    try:
        if key_binding and not key_binding.startswith('mouse:'):
            key_char = key.char if hasattr(key, 'char') and key.char else str(key).replace("Key.", "").lower()
            if key_char == key_binding.lower():
                toggle_state()
    except Exception as e:
        error_log(f"Error in on_key_press: {e}")

def on_mouse_press(x, y, button, pressed):
    global key_binding
    if pressed and key_binding == f"mouse:{button.name}":
        toggle_state()

def input_listener():
    def on_press(key):
        if not bind_event.is_set():
            k = key.char if hasattr(key, 'char') and key.char else str(key).replace("Key.", "")
            window.write_event_value('-KEYBIND_UPDATE-', k)
            bind_event.set()
            return False

    def on_click(x, y, button, pressed):
        if pressed and not bind_event.is_set():
            window.write_event_value('-KEYBIND_UPDATE-', f"mouse:{button.name}")
            bind_event.set()
            return False

    with KeyboardListener(on_press=on_press) as k_listener, MouseListener(on_click=on_click) as m_listener:
        k_listener.join()
        m_listener.join()

def create_window():
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('L3TH4L-R3M0T3')
    sg.ChangeLookAndFeel('DarkGrey1')

    image_size = (100, 100)
    image_column = [[sg.Image(normal, key='-IMAGE-', size=image_size, expand_x=True, expand_y=True)]]
    text_column = [
        [sg.Text('Your local address is: ' + resolve_address(), text_color='black')],
        [sg.Text('Set remote computer ip:', text_color='black'), sg.Input(check_config()[0], size=(15), key='-IP-', text_color='black')],
        [sg.Text('Key binding', text_color='black'), sg.Text(check_config()[1] if check_config()[1] else 'Not set', size=20, key='-KEYBIND-', text_color='black')],
        [sg.Text('Status: ', size=(5, 1), text_color='black'), sg.Text('Waiting for connection...', key='-OUTPUT-', text_color='black')]
    ]
    layout = [[sg.Frame('', text_column, border_width=0), sg.Frame('', image_column, border_width=0)],
              [sg.Button('Connect', button_color='black'),
               sg.Button('Bind Key', button_color='black'),
               sg.Button('Save', button_color='black'),
               sg.Button('Quit/Disconnect', button_color='black')]]
    return sg.Window("L3TH4L-R3M0T3", layout, icon=icon_path, finalize=True, resizable=False)

def main():
    global listener
    while True:
        event, values = window.read()
        if event == 'UPDATE_IMAGE':
            new_state = values[event]
            window['-IMAGE-'].update(filename=muted if new_state == 'muted' else unmuted)
        if event == '-KEYBIND_UPDATE-':
            global key_binding
            key_binding = values[event]
            window['-KEYBIND-'].update(key_binding)
        if event == 'Connect':
            window['-OUTPUT-'].set_focus()
            target_ip = str(values['-IP-'])
            validate_ip(target_ip, local_ip)
            window['-OUTPUT-'].update('Connected to L3TH4L-L1573N.')
            if not key_binding:
                window['-OUTPUT-'].update('No key bound. Please bind key first!')
            elif is_port_open(target_ip, PORT):
                if listener is None:
                    listener = KeyboardListener(on_press=on_key_press)
                    listener.start()
                    MouseListener(on_click=on_mouse_press).start()
            else:
                window['-OUTPUT-'].update("Target is offline ¯\\_(ツ)_/¯")
        if event == 'Bind Key':
            bind_event.clear()
            sg.popup_auto_close("Press any key or mouse button...", auto_close=False, non_blocking=True, modal=False)
            threading.Thread(target=input_listener, daemon=True).start()
        if event == 'Save':
            save_config(str(values['-IP-']), key_binding)
        if event == "Quit/Disconnect" or event == sg.WIN_CLOSED:
            on_disconnect()
            if listener:
                listener.stop()
            listener = None
            break
    window.close()

if __name__ == '__main__':
    target_ip, key_binding = check_config()
    #print(f"Loaded Key Binding: {key_binding}")
    window = create_window()
    window.set_icon(icon_path)
    local_ip = resolve_address()
    main()
