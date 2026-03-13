import socket
import threading

HOST = '127.0.0.1'
PORT = 5555

clients = {}
clients_lock = threading.Lock()

def handle_client(client_socket, address):
    username = None  # Khởi tạo biến để tránh lỗi khi vào khối finally
    try:
        # Bước 1: Yêu cầu Client gửi username
        data = client_socket.recv(1024)
        if not data:
            return
            
        username = data.decode('utf-8').strip()
        
        with clients_lock:
            if username in clients:
                client_socket.send("ERROR: Username đã tồn tại. Hãy thử lại bằng tên khác.".encode('utf-8'))
                username = None 
                return 
            
            # Thêm user vào danh sách nếu tên hợp lệ
            clients[username] = client_socket
        
        # IN RA SERVER ĐỂ KIỂM TRA
        print(f"[+] {username} đã kết nối. Hiện có {len(clients)} người đang online.")
        client_socket.send("SUCCESS".encode('utf-8'))

        # Lắng nghe tin nhắn từ client
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            
            message = data.decode('utf-8').strip()
            
            if message == "/list":
                with clients_lock:
                    online_users = ", ".join(clients.keys())
                    total_count = len(clients)
                client_socket.send(f"[SERVER] Có {total_count} người dùng đang online: {online_users}".encode('utf-8'))
            
            elif message.startswith("/msg "):
                parts = message.split(' ', 2)
                if len(parts) == 3:
                    target_user = parts[1]
                    msg_content = parts[2]
                    
                    with clients_lock:
                        if target_user in clients:
                            target_socket = clients[target_user]
                            try:
                                target_socket.send(f"\n[From {username}]: {msg_content}".encode('utf-8'))
                                client_socket.send(f"[Me -> {target_user}]: {msg_content}".encode('utf-8'))
                            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                                # Nếu target đã ngắt kết nối, đóng socket và loại khỏi danh sách
                                try:
                                    target_socket.close()
                                except Exception:
                                    pass
                                del clients[target_user]
                        else:
                            client_socket.send(f"[SERVER] Không tìm thấy '{target_user}'.".encode('utf-8'))
                else:
                    client_socket.send("[SERVER] Sai cú pháp. Dùng: /msg <username> <nội dung>".encode('utf-8'))
            
            elif message.startswith("/all "):
                parts = message.split(' ', 1)
                if len(parts) == 2 and parts[1].strip():
                    msg_content = parts[1]
                    with clients_lock:
                        for user, sock in list(clients.items()):
                            if user != username:
                                try:
                                    sock.send(f"\n[{username}]: {msg_content}".encode('utf-8'))
                                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                                    # Loại bỏ client đã ngắt kết nối để tránh lỗi 10054
                                    try:
                                        sock.close()
                                    except Exception:
                                        pass
                                    del clients[user]
                else:
                    client_socket.send("[SERVER] Sai cú pháp. Dùng: /all <nội dung>".encode('utf-8'))
            else:
                client_socket.send("[SERVER] Errol!!!".encode('utf-8'))

    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
        pass
    except Exception as e:
        # Log lỗi khác để dễ tìm nguyên nhân
        print(f"[!] Lỗi kết nối với {address}: {e}")
    finally:
        # Khi client ngắt kết nối (bất kể lý do gì)
        if username:
            with clients_lock:
                if username in clients:
                    del clients[username]
            print(f"[-] {username} đã ngắt kết nối. Còn lại {len(clients)} người.")
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Thêm dòng này để tránh lỗi "Port is already in use" khi restart server liên tục
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server.bind((HOST, PORT))
    
    # Cho phép hàng đợi lên tới 10 kết nối cùng lúc
    server.listen(10) 
    print(f"[*] Server đang chạy tại {HOST}:{PORT}")

    try:
        while True:
            client_socket, address = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, address))
            thread.daemon = True # Thread tự đóng khi tắt server
            thread.start()
    except KeyboardInterrupt:
        # Cho phép dừng server bằng Ctrl+C từ terminal
        print("\n[!] Dừng server ")
    finally:
        server.close()
        print("[*] Server đã dừng.")

if __name__ == "__main__":
    start_server()