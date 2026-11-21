import socket, ssl, struct, threading, datetime, sys

LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 9100
PRINTER_HOST = '192.168.1.55'
PRINTER_PORT = 631
PRINTER_URI = 'ipp://192.168.1.55:631/ipp/print'
LOG = r'C:\Users\alpha\ipp_bridge.log'

def log(msg):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

def attr(tag, name, value):
    n = name.encode(); v = value.encode()
    return bytes([tag]) + struct.pack('>H', len(n)) + n + struct.pack('>H', len(v)) + v

def build_print_job(data, job_name):
    header = struct.pack('>HHI', 0x0101, 0x0002, 1)  # IPP 1.1, Print-Job
    attrs = b''
    attrs += attr(0x47, 'attributes-charset', 'utf-8')
    attrs += attr(0x48, 'attributes-natural-language', 'en')
    attrs += attr(0x45, 'printer-uri', PRINTER_URI)
    attrs += attr(0x42, 'requesting-user-name', 'windows')
    attrs += attr(0x42, 'job-name', job_name)
    attrs += attr(0x49, 'document-format', 'application/vnd.epson.escpr')
    return header + bytes([0x01]) + attrs + bytes([0x03]) + data

def forward_to_printer(data, job_name):
    req = build_print_job(data, job_name)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection((PRINTER_HOST, PRINTER_PORT), timeout=30) as raw:
        s = ctx.wrap_socket(raw)
        http = (f"POST /ipp/print HTTP/1.1\r\nHost: {PRINTER_HOST}:{PRINTER_PORT}\r\n"
                f"Content-Type: application/ipp\r\nContent-Length: {len(req)}\r\n"
                f"Connection: close\r\n\r\n").encode() + req
        s.sendall(http)
        resp = b''
        while True:
            try:
                chunk = s.recv(4096)
            except Exception:
                break
            if not chunk:
                break
            resp += chunk
    status = struct.unpack('>H', resp.split(b'\r\n')[0] and resp[resp.find(b'\r\n')+2:][2:4])[0] if len(resp) > 10 else -1
    # extrait le statut IPP (octets 2-3 du corps, apres la ligne de statut HTTP et headers) -> on parse le body
    body = resp.split(b'\r\n\r\n', 1)[1] if b'\r\n\r\n' in resp else resp
    ipp_status = struct.unpack('>H', body[2:4])[0] if len(body) >= 4 else -1
    return ipp_status

def handle(conn, addr):
    try:
        conn.settimeout(60)
        data = b''
        while True:
            try:
                chunk = conn.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        if not data:
            log(f"{addr}: connexion vide, ignore")
            return
        # Ignore les sondes du moniteur de port Windows (petites trames < 1 Ko)
        if len(data) < 1024:
            return
        log(f"{addr}: recu {len(data)} octets, envoi a l'imprimante...")
        status = forward_to_printer(data, f'windows-job-{addr[1]}')
        log(f"{addr}: statut IPP 0x{status:04X} ({'OK' if status == 0 else 'ERREUR'})")
    except Exception as e:
        log(f"{addr}: ERREUR {e}")
    finally:
        conn.close()

def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((LISTEN_HOST, LISTEN_PORT))
    srv.listen(10)
    log(f"Pont IPP demarre sur {LISTEN_HOST}:{LISTEN_PORT} -> {PRINTER_HOST}:{PRINTER_PORT}")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()

if __name__ == '__main__':
    main()
