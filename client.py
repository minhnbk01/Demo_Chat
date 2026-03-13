import socket
import threading
import sys

# Cấu hình kết nối tới Server
HOST = '127.0.0.1'
PORT = 5555

def receive_messages(client_socket):
    """Luồng luôn chạy ngầm để nhận tin nhắn từ Server"""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            
            # Xóa dòng prompt hiện tại, in tin nhắn, và in lại dòng prompt
            print(f"\r{message}\n>> ", end="", flush=True)
        except:
            print("\n[!] Mất kết nối tới Server.")
            client_socket.close()
            sys.exit(0)

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
    except Exception as e:
        print(f"Không thể kết nối tới Server: {e}")
        return

    # Quá trình Login
    while True:
        username = input("Nhập username để login: ")
        if not username.strip():
            print("[!] Username không được để trống!")
            continue
        client.send(username.encode('utf-8'))
        response = client.recv(1024).decode('utf-8')
        
        if response == "SUCCESS":
            print(f"[*] Đăng nhập thành công với tên '{username}'!")
            break
        else:
            print(response)
            client.close()
            return

    print("\n--- CÁC LỆNH HỖ TRỢ ---")
    print("/list                 : Xem danh sách user online")
    print("/msg <user> <tin_nhắn>: Nhắn tin riêng cho 1 user")
    print("/all <tin_nhắn>       : Nhắn tin cho toàn bộ room")
    print("/quit                 : Thoát ứng dụng")
    print("-----------------------\n")

    # Khởi chạy luồng nhận tin nhắn
    recv_thread = threading.Thread(target=receive_messages, args=(client,))
    recv_thread.daemon = True
    recv_thread.start()

    # Luồng chính: Nhận input từ bàn phím
    while True:
        try:
            command = input(">> ")
            if not command.strip():
                continue
                
            if command == "/quit":
                client.close()
                sys.exit(0)
            
            # Gửi lệnh lên Server
            client.send(command.encode('utf-8'))
            
        except KeyboardInterrupt:
            print("\nĐang thoát...")
            client.close()
            sys.exit(0)

if __name__ == "__main__":
    start_client()
