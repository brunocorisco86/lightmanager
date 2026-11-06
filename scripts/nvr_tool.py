#!/usr/bin/env python3
"""
Utilitário CLI somente-leitura (read-only) para diagnóstico e escuta de eventos
de Detecção Humana no NVR XiongMai (192.168.1.20:34567) via protocolo binário DVRIP.
Zero dependências externas (usa apenas a biblioteca padrão do Python).
"""
import argparse
import hashlib
import json
import os
import select
import socket
import struct
import sys
import time
from datetime import datetime

DEFAULT_NVR_HOST = os.getenv("NVR_HOST", "192.168.1.20")
DEFAULT_NVR_PORT = int(os.getenv("NVR_PORT", "34567"))
DEFAULT_NVR_USER = os.getenv("NVR_USER", "brunoconter")
DEFAULT_NVR_PASS = os.getenv("NVR_PASS", "blurbang")


def xm_md5(password: str) -> str:
    """Calcula o hash MD5 proprietário de 8 caracteres em base62 da XiongMai (Sofia)."""
    d = hashlib.md5(password.encode("utf-8")).digest()
    out = []
    for i in range(8):
        v = (d[2 * i] + d[2 * i + 1]) % 62
        if v < 10:
            out.append(chr(48 + v))
        elif v < 36:
            out.append(chr(55 + v))
        else:
            out.append(chr(61 + v))
    return "".join(out)


class DVRIPClient:
    """Cliente leve TCP DVRIP (somente-leitura e recepção de eventos Guard/AlarmInfo)."""

    def __init__(self, host: str, port: int = 34567, user: str = "brunoconter", password: str = "blurbang", timeout: float = 5.0):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout
        self.sock: socket.socket | None = None
        self.session_id: int = 0
        self.session_hex: str = "0x00000000"
        self.seq: int = 0
        self.login_info: dict = {}

    def connect_and_login(self) -> dict:
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        login_pkt = {
            "EncryptType": "MD5",
            "LoginType": "DVRIP-Web",
            "PassWord": xm_md5(self.password),
            "UserName": self.user,
        }
        (_, sess), data = self.request(1000, login_pkt)
        if data.get("Ret") != 100:
            raise RuntimeError(f"Falha no login DVRIP ({self.host}:{self.port}): Ret={data.get('Ret')} -> {data}")
        self.session_id = sess
        self.session_hex = data.get("SessionID", f"0x{sess:08x}")
        self.login_info = data
        return data

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def send_packet(self, msg_id: int, payload_dict: dict):
        if not self.sock:
            raise RuntimeError("Socket DVRIP não conectado")
        body = json.dumps(payload_dict).encode("utf-8") + b"\x0a\x00"
        hdr = struct.pack("<BB2xII2xHI", 0xff, 0x00, self.session_id, self.seq, msg_id, len(body))
        self.seq += 1
        self.sock.sendall(hdr + body)

    def recv_packet(self) -> tuple[tuple[int, int], dict]:
        if not self.sock:
            raise RuntimeError("Socket DVRIP não conectado")
        resp_hdr = self._recv_exact(20)
        head, ver, sess, rseq, rmsg, rlen = struct.unpack("<BB2xII2xHI", resp_hdr)
        raw_body = self._recv_exact(rlen) if rlen > 0 else b"{}"
        text = raw_body.rstrip(b"\x00\x0a").decode("utf-8", errors="replace")
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = {"raw": text}
        return (rmsg, sess), parsed

    def _recv_exact(self, num_bytes: int) -> bytes:
        buf = b""
        while len(buf) < num_bytes:
            chunk = self.sock.recv(num_bytes - len(buf))
            if not chunk:
                raise ConnectionError("Conexão encerrada pelo NVR")
            buf += chunk
        return buf

    def request(self, msg_id: int, payload_dict: dict) -> tuple[tuple[int, int], dict]:
        self.send_packet(msg_id, payload_dict)
        return self.recv_packet()

    def get_config(self, name: str) -> dict:
        _, res = self.request(1042, {"Name": name, "SessionID": self.session_hex})
        return res


def get_nvr_channels_summary(host=DEFAULT_NVR_HOST, port=DEFAULT_NVR_PORT, user=DEFAULT_NVR_USER, password=DEFAULT_NVR_PASS, timeout=3.0) -> list[dict]:
    """Retorna lista estruturada dos 9 canais do NVR (somente-leitura)."""
    client = DVRIPClient(host, port, user, password, timeout=timeout)
    try:
        client.connect_and_login()
        st_res = client.get_config("NetWork.ChnStatus")
        rem_res = client.get_config("NetWork.RemoteDeviceV3")
        chn_status = st_res.get("NetWork.ChnStatus", [])
        rem_devs = rem_res.get("NetWork.RemoteDeviceV3", [])

        channels = []
        for idx in range(9):
            ch_num = idx + 1
            st = chn_status[idx] if idx < len(chn_status) else {}
            rem = rem_devs[idx] if idx < len(rem_devs) else {}
            dec = (rem.get("Decoder") or [{}])[0]
            hd_res = client.get_config(f"Detect.HumanDetection.[{idx}]")
            hd_cfg = hd_res.get(f"Detect.HumanDetection.[{idx}]", {})
            human_enabled = bool(hd_cfg.get("Enable", False)) if hd_res.get("Ret") == 100 else False

            channels.append({
                "channel": ch_num,
                "index": idx,
                "code": f"D{ch_num:02d}",
                "status": st.get("Status", "Unknown"),
                "resolution": st.get("CurRes", "Unknown"),
                "enabled": bool(rem.get("Enable", False)),
                "ip": dec.get("IPAddress"),
                "mac": dec.get("MacAddr"),
                "protocol": dec.get("Protocol"),
                "human_detection": human_enabled,
            })
        return channels
    finally:
        client.close()


def cmd_status(args):
    client = DVRIPClient(args.host, args.port, args.user, args.password)
    try:
        client.connect_and_login()
        _, sys_res = client.request(1020, {"Name": "SystemInfo", "SessionID": client.session_hex})
        _, time_res = client.request(1452, {"Name": "OPTimeQuery", "SessionID": client.session_hex})
        sys_info = sys_res.get("SystemInfo", {})
        print(f"=== 🖥️  NVR XiongMai ({args.host}:{args.port}) ===")
        print(f"Placa / Modelo : {sys_info.get('HardWare')} (Canais Digitais: {sys_info.get('DigChannel')})")
        print(f"Firmware       : {sys_info.get('SoftWareVersion')} (Build: {sys_info.get('BuildTime')})")
        print(f"Serial Number  : {sys_info.get('SerialNo')}")
        print(f"Relógio Interno: {time_res.get('OPTimeQuery')}")
        print("\n=== 📹 Canais Configurados ===")
    finally:
        client.close()

    channels = get_nvr_channels_summary(args.host, args.port, args.user, args.password)
    print(f"{'Canal':<6} | {'Status':<10} | {'Resolução':<14} | {'IP Câmera':<14} | {'MAC Address':<18} | {'Proto':<6} | {'IA Humana'}")
    print("-" * 92)
    for ch in channels:
        hd_badge = "✅ ATIVA" if ch["human_detection"] else "—"
        print(
            f"{ch['code']:<6} | {str(ch['status']):<10} | {str(ch['resolution']):<14} | "
            f"{str(ch['ip'] or '-'):<14} | {str(ch['mac'] or '-'):<18} | {str(ch['protocol'] or '-'):<6} | {hd_badge}"
        )


def cmd_human_config(args):
    client = DVRIPClient(args.host, args.port, args.user, args.password)
    try:
        client.connect_and_login()
        for idx in range(9):
            res = client.get_config(f"Detect.HumanDetection.[{idx}]")
            if res.get("Ret") == 100:
                cfg = res.get(f"Detect.HumanDetection.[{idx}]", {})
                rules = [r for r in cfg.get("PedRule", []) if r.get("Enable")]
                pts = rules[0].get("RuleRegion", {}).get("Pts", []) if rules else []
                print(f"Canal D{idx+1:02d} (idx={idx}): Enable={cfg.get('Enable')} | Sensitivity={cfg.get('Sensitivity')} | Polígono ({len(pts)} pts): {pts}")
    finally:
        client.close()


def cmd_listen(args):
    client = DVRIPClient(args.host, args.port, args.user, args.password, timeout=10.0)
    try:
        client.connect_and_login()
        _, guard_res = client.request(1500, {"SessionID": client.session_hex})
        print(f"🛡️  Guard assinado em {args.host}:{args.port} (Ret={guard_res.get('Ret')}). Escutando eventos (Ctrl+C para sair)...")
        last_ka = time.time()
        while True:
            rlist, _, _ = select.select([client.sock], [], [], 1.0)
            if rlist:
                (rmsg, _), pkt = client.recv_packet()
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if rmsg == 1504 or "AlarmInfo" in pkt:
                    info = pkt.get("AlarmInfo", pkt)
                    ch_idx = info.get("Channel", -1)
                    ch_code = f"D{ch_idx + 1:02d}" if isinstance(ch_idx, int) and ch_idx >= 0 else str(ch_idx)
                    print(f"[{now_str}] 🚨 ALARME {ch_code} | Evento={info.get('Event')} | Status={info.get('Status')} | HoraNVR={info.get('StartTime')}")
                elif rmsg != 1007:
                    print(f"[{now_str}] 📩 msg_id={rmsg}: {pkt}")

            if time.time() - last_ka >= 18.0:
                client.send_packet(1006, {"Name": "KeepAlive", "SessionID": client.session_hex})
                last_ka = time.time()
    except KeyboardInterrupt:
        print("\nEncerrando escuta do NVR.")
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description="Ferramenta CLI Somente-Leitura do NVR XiongMai")
    parser.add_argument("--host", default=DEFAULT_NVR_HOST, help="IP do NVR (padrão: 192.168.1.20)")
    parser.add_argument("--port", type=int, default=DEFAULT_NVR_PORT, help="Porta DVRIP (padrão: 34567)")
    parser.add_argument("--user", default=DEFAULT_NVR_USER, help="Usuário do NVR")
    parser.add_argument("--password", default=DEFAULT_NVR_PASS, help="Senha do NVR")

    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="Exibe informações do NVR e status dos 9 canais")
    sub.add_parser("human-config", help="Exibe configurações de Detecção Humana por IA nos canais ativos")
    sub.add_parser("listen", help="Escuta eventos de alarme/detecção humana em tempo real (Guard 1500)")

    args = parser.parse_args()
    if args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "human-config":
        cmd_human_config(args)
    elif args.cmd == "listen":
        cmd_listen(args)


if __name__ == "__main__":
    main()
