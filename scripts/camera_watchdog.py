#!/usr/bin/env python3
"""
Watchdog de Saúde e Self-Healing das Câmeras IP e NVR XiongMai integrado ao LanSentry.

Funcionalidades:
1. Consulta o catálogo de ativos do LanSentry (http://192.168.1.7:8840/api/all) por MAC Address.
2. Executa descoberta broadcast Layer-2 UDP (porta 34569/34568, msg_id=1530 -> 1531).
3. Mede a saúde e latência real (ms) de login DVRIP (34567/tcp) e ONVIF (5000/tcp) de cada câmera.
4. Detecta problemas mapeados:
   - Mudança de IP via DHCP após reboot de roteador (ex: D02, D05)
   - Perda de configuração no NVR (NoConfig) ou erro de credencial (NoLogin / Ret=203)
   - Bloqueio temporário de segurança da câmera (Ret=206 Account Locked)
   - Preenchimento indevido de MacAddr em canais de IP estático secundário (.201/.204/.206)
     que faz o NVR disparar pacotes UDP 1532 e derrubar a rota Wi-Fi (wlan0) das câmeras GK7202V300.
5. Aplica Self-Healing automático em NetWork.RemoteDeviceV3 no NVR (192.168.1.20) quando necessário.
"""

import argparse
import copy
import json
import os
import select
import socket
import struct
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.nvr_tool import (
    DEFAULT_NVR_HOST,
    DEFAULT_NVR_PASS,
    DEFAULT_NVR_PORT,
    DEFAULT_NVR_USER,
    DVRIPClient,
)

# Fuso horário de Brasília (GMT-3) obrigatório conforme regras do projeto
SP_TZ = timezone(timedelta(hours=-3))

DEFAULT_LANSENTRY_URL = os.getenv("LANSENTRY_API_URL", "http://192.168.1.7:8840/api/all")

# Catálogo canônico das 6 câmeras instaladas
CAMERA_CATALOG = [
    {
        "channel": 1,
        "index": 0,
        "code": "D01",
        "name": "Câmera D01 (iComm XM530)",
        "preferred_ip": "192.168.1.201",
        "lan_mac": "d4:a3:eb:89:bd:f4",
        "xm_mac": "d4:a3:eb:89:bd:f4",
        "port": 34567,
        "protocol": "TCP",
        "user": "kxhu",
        "password": "7prkra",
        "wifi_ap": "quarto (192.168.1.44)",
        "nvr_mac_policy": "empty",  # Evita que o NVR sobrescreva .201 com o IP DHCP (.13)
    },
    {
        "channel": 2,
        "index": 1,
        "code": "D02",
        "name": "Câmera D02 (XM210 V5.08)",
        "preferred_ip": "192.168.1.4",  # IP habitual no Wi-Fi; rastreado via LanSentry + UDP 1531
        "lan_mac": "f8:16:0c:96:d5:f6",
        "xm_mac": "00:13:00:f6:69:a0",
        "port": 34567,
        "protocol": "TCP",
        "user": "bruno",
        "password": "blurbang86",
        "wifi_ap": "ZN-BRUNO_CONTER (192.168.1.1)",
        "nvr_mac_policy": "xm_mac",  # Permite ao NVR rastrear o IP via MAC interno 00:13:00:f6:69:a0
    },
    {
        "channel": 3,
        "index": 2,
        "code": "D03",
        "name": "Câmera D03 (XM530 1080P IA)",
        "preferred_ip": "192.168.1.203",
        "lan_mac": "00:13:00:01:61:7b",
        "xm_mac": "00:13:00:01:61:7b",
        "port": 34567,
        "protocol": "TCP",
        "user": "usma",
        "password": "n2ykyy",
        "wifi_ap": "Cabeada / Static",
        "nvr_mac_policy": "xm_mac",
    },
    {
        "channel": 4,
        "index": 3,
        "code": "D04",
        "name": "Câmera D04 (GK7202V300 4MP IA)",
        "preferred_ip": "192.168.1.204",
        "lan_mac": "38:be:ab:91:96:85",
        "xm_mac": "38:be:ab:91:96:85",
        "port": 34567,
        "protocol": "TCP",
        "user": "admin",
        "password": "23blurbang86",
        "wifi_ap": "quarto (192.168.1.44)",
        "nvr_mac_policy": "empty",  # CRÍTICO: manter vazio para o NVR não enviar UDP 1532
    },
    {
        "channel": 5,
        "index": 4,
        "code": "D05",
        "name": "Câmera D05 (Trolink ONVIF)",
        "preferred_ip": "192.168.1.3",
        "lan_mac": "48:8f:4c:3d:13:14",
        "xm_mac": None,
        "port": 5000,
        "protocol": "ONVIF",
        "user": "admin",
        "password": "23blurbang86",
        "wifi_ap": "ZN-BRUNO_CONTER (192.168.1.1)",
        "nvr_mac_policy": "lan_mac",
    },
    {
        "channel": 6,
        "index": 5,
        "code": "D06",
        "name": "Câmera D06 (GK7202V300 Vizinho IA)",
        "preferred_ip": "192.168.1.206",
        "lan_mac": "a4:ef:15:30:79:32",
        "xm_mac": "a4:ef:15:30:79:32",
        "port": 34567,
        "protocol": "TCP",
        "user": "admin",
        "password": "23blurbang",
        "wifi_ap": "quarto (192.168.1.44)",
        "nvr_mac_policy": "empty",  # CRÍTICO: manter vazio para o NVR não enviar UDP 1532
    },
]


def hex_ip_to_str(hex_ip: str | None) -> str | None:
    """Converte IP hexadecimal little-endian da XiongMai (ex: '0x0401A8C0') para '192.168.1.4'."""
    if not hex_ip or not isinstance(hex_ip, str) or not hex_ip.startswith("0x") or len(hex_ip) != 10:
        return None
    try:
        val = int(hex_ip, 16)
        b1 = val & 0xFF
        b2 = (val >> 8) & 0xFF
        b3 = (val >> 16) & 0xFF
        b4 = (val >> 24) & 0xFF
        return f"{b1}.{b2}.{b3}.{b4}"
    except Exception:
        return None


def fetch_lansentry_mac_map(api_url: str = DEFAULT_LANSENTRY_URL, timeout: float = 4.0) -> dict[str, dict]:
    """
    Consulta a API do LanSentry e retorna um dicionário {mac_lower: {"ip": ..., "online": ..., "date": ...}}
    priorizando registros ativos (Now == 1) ou mais recentes.
    """
    mac_map: dict[str, dict] = {}
    try:
        with urllib.request.urlopen(api_url, timeout=timeout) as resp:
            hosts = json.loads(resp.read().decode("utf-8", errors="replace"))
        for h in hosts:
            mac = (h.get("Mac") or "").strip().lower()
            ip = (h.get("IP") or "").strip()
            if not mac or not ip:
                continue
            online = int(h.get("Now") or 0)
            date_str = str(h.get("Date") or "")
            existing = mac_map.get(mac)
            if not existing or (online > existing["online"]) or (online == existing["online"] and date_str > existing["date"]):
                mac_map[mac] = {"ip": ip, "online": online, "date": date_str, "name": h.get("Name") or ""}
    except Exception as e:
        print(f"⚠️ [LANSENTRY] Aviso ao consultar {api_url}: {e}")
    return mac_map


def discover_xiongmai_udp(timeout: float = 2.0) -> dict[str, dict]:
    """
    Envia broadcast UDP msg_id=1530 na porta 34569 e escuta respostas msg_id=1531 (34568/34569).
    Retorna {xm_mac_lower: {"ip": sender_ip, "host_ip": decoded_host_ip, "raw": NetCommon}}.
    """
    discovered: dict[str, dict] = {}
    sockets = []
    try:
        for port in (34568, 34569):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("", port))
            sockets.append(s)

        pkt = struct.pack("<BB2xII2xHI", 0xFF, 0x00, 0, 0, 1530, 0)
        for dst in ("255.255.255.255", "192.168.1.255"):
            try:
                sockets[-1].sendto(pkt, (dst, 34569))
            except Exception:
                pass

        t0 = time.time()
        while time.time() - t0 < timeout:
            rlist, _, _ = select.select(sockets, [], [], 0.25)
            for sock in rlist:
                try:
                    data, addr = sock.recvfrom(4096)
                    if len(data) <= 20:
                        continue
                    _, _, _, _, msg_id, _ = struct.unpack("<BB2xII2xHI", data[:20])
                    if msg_id == 1531:
                        text = data[20:].rstrip(b"\x00\x0a").decode("utf-8", errors="replace")
                        body = json.loads(text)
                        nc = body.get("NetWork.NetCommon", {})
                        mac = (nc.get("MAC") or "").strip().lower()
                        if mac and mac not in discovered:
                            discovered[mac] = {
                                "ip": addr[0],
                                "host_ip": hex_ip_to_str(nc.get("HostIP")) or addr[0],
                                "raw": nc,
                            }
                except Exception:
                    pass
    except Exception as e:
        print(f"⚠️ [UDP-1530] Aviso na descoberta broadcast: {e}")
    finally:
        for s in sockets:
            try:
                s.close()
            except Exception:
                pass
    return discovered


def probe_camera_endpoint(ip: str, port: int, protocol: str, user: str, password: str, timeout: float = 3.5, retries: int = 2) -> dict:
    """
    Testa a conectividade e autenticação real de uma câmera em um IP específico
    com retry contra jitter momentâneo de Wi-Fi.
    Retorna {"ok": bool, "latency_ms": float | None, "error": str | None, "locked_206": bool}.
    """
    if not ip:
        return {"ok": False, "latency_ms": None, "error": "no_ip", "locked_206": False}

    last_err = None
    for _ in range(max(1, retries)):
        t0 = time.perf_counter()
        if protocol.upper() == "ONVIF" or port == 5000:
            try:
                s = socket.create_connection((ip, port), timeout=timeout)
                s.close()
                lat = round((time.perf_counter() - t0) * 1000.0, 1)
                return {"ok": True, "latency_ms": lat, "error": None, "locked_206": False}
            except Exception as e:
                last_err = str(e)
                time.sleep(0.2)
                continue

        client = DVRIPClient(ip, port, user, password, timeout=timeout)
        try:
            client.connect_and_login()
            lat = round((time.perf_counter() - t0) * 1000.0, 1)
            return {"ok": True, "latency_ms": lat, "error": None, "locked_206": False}
        except Exception as e:
            err_str = str(e)
            if "Ret=206" in err_str:
                return {"ok": False, "latency_ms": None, "error": err_str, "locked_206": True}
            if "Ret=203" in err_str or "Ret=205" in err_str:
                return {"ok": False, "latency_ms": None, "error": err_str, "locked_206": False}
            last_err = err_str
            time.sleep(0.2)
        finally:
            client.close()

    return {"ok": False, "latency_ms": None, "error": last_err, "locked_206": False}


def expected_nvr_mac(cam: dict) -> str:
    """Retorna o valor esperado do campo MacAddr no NVR conforme a política de cada câmera."""
    policy = cam.get("nvr_mac_policy", "empty")
    if policy == "xm_mac":
        return cam.get("xm_mac") or ""
    if policy == "lan_mac":
        return cam.get("lan_mac") or ""
    return ""


def build_decoder_entry(cam: dict, target_ip: str, template_entry: dict | None = None) -> dict:
    """Constrói a estrutura de canal para NetWork.RemoteDeviceV3[idx]."""
    if template_entry and isinstance(template_entry, dict) and template_entry.get("Decoder"):
        entry = copy.deepcopy(template_entry)
        dec = entry["Decoder"][0]
    else:
        dec = {
            "Channel": 0,
            "ConfName": "chConfig",
            "DevType": "IPC",
            "Enable": True,
            "IPAddress": target_ip,
            "Interval": 10,
            "MacAddr": "",
            "MainRtspUrl": "",
            "PassWord": cam["password"],
            "Port": cam["port"],
            "Protocol": cam["protocol"],
            "SerialNo": "",
            "StreamType": "MAIN",
            "SubRtspUrl": "",
            "TransModel": 0,
            "UserName": cam["user"],
        }
        entry = {
            "ConnType": "SINGLE",
            "Decoder": [dec],
            "EnCheckTime": True,
            "Enable": True,
            "SingleConnId": "0x00000001",
            "SynchResolution": False,
            "TourIntv": 10,
        }

    entry["Enable"] = True
    entry["SingleConnId"] = "0x00000001"
    dec["Enable"] = True
    dec["IPAddress"] = target_ip
    dec["Port"] = cam["port"]
    dec["Protocol"] = cam["protocol"]
    dec["UserName"] = cam["user"]
    dec["PassWord"] = cam["password"]
    dec["MacAddr"] = expected_nvr_mac(cam)
    return entry


def evaluate_and_heal(
    nvr_host: str = DEFAULT_NVR_HOST,
    nvr_port: int = DEFAULT_NVR_PORT,
    nvr_user: str = DEFAULT_NVR_USER,
    nvr_pass: str = DEFAULT_NVR_PASS,
    lansentry_url: str = DEFAULT_LANSENTRY_URL,
    apply_heal: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Executa a auditoria completa de saúde das 6 câmeras cruzando NVR, LanSentry e UDP 1530,
    e opcionalmente aplica Self-Healing no NVR.
    """
    now_str = datetime.now(SP_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"==========================================================================================")
    print(f"🛡️  Camera Watchdog & LanSentry Self-Heal [{now_str}]")
    print(f"==========================================================================================")

    lan_map = fetch_lansentry_mac_map(lansentry_url)
    udp_map = discover_xiongmai_udp()

    nvr = DVRIPClient(nvr_host, nvr_port, nvr_user, nvr_pass, timeout=4.0)
    nvr.connect_and_login()
    try:
        st_res = nvr.get_config("NetWork.ChnStatus")
        rem_res = nvr.get_config("NetWork.RemoteDeviceV3")
        chn_status = st_res.get("NetWork.ChnStatus", [])
        rem_devs = rem_res.get("NetWork.RemoteDeviceV3", [])

        report_rows = []
        actions_taken = []
        rem_modified = False

        header = (
            f"{'Canal':<5} | {'Status NVR':<10} | {'IP no NVR':<14} | {'IP LanSentry':<14} | "
            f"{'IP UDP 1531':<14} | {'Saúde / Latência':<18} | {'Ação / Diagnóstico'}"
        )
        print(header)
        print("-" * len(header))

        for cam in CAMERA_CATALOG:
            idx = cam["index"]
            code = cam["code"]
            st = chn_status[idx] if idx < len(chn_status) else {}
            rem = rem_devs[idx] if idx < len(rem_devs) else {}
            dec = (rem.get("Decoder") or [{}])[0] if rem.get("Decoder") else {}

            nvr_status = st.get("Status", "Unknown")
            nvr_ip = dec.get("IPAddress") or ""
            nvr_mac = dec.get("MacAddr") or ""
            nvr_user_cfg = dec.get("UserName") or ""
            nvr_pass_cfg = dec.get("PassWord") or ""
            nvr_enabled = bool(rem.get("Enable", False))

            lan_info = lan_map.get((cam["lan_mac"] or "").lower(), {})
            lan_ip = lan_info.get("ip") or ""

            udp_info = udp_map.get((cam["xm_mac"] or "").lower(), {})
            udp_ip = udp_info.get("ip") or ""

            # Ordem de candidatos de IP para testar saúde da câmera:
            # 1. IP preferencial fixo (.201, .203, .204, .206, .3)
            # 2. IP atual configurado no NVR
            # 3. IP descoberto via UDP 1531 broadcast
            # 4. IP descoberto via LanSentry (MAC Layer-2)
            candidate_ips = []
            for cand in (cam["preferred_ip"], nvr_ip, udp_ip, lan_ip):
                if cand and cand not in candidate_ips:
                    candidate_ips.append(cand)

            best_ip = None
            best_probe = {"ok": False, "latency_ms": None, "error": "unreachable", "locked_206": False}

            for cand_ip in candidate_ips:
                probe = probe_camera_endpoint(
                    cand_ip, cam["port"], cam["protocol"], cam["user"], cam["password"]
                )
                if probe["ok"]:
                    best_ip = cand_ip
                    best_probe = probe
                    break
                if best_probe["error"] == "unreachable" or probe["locked_206"]:
                    best_probe = probe

            target_ip = best_ip or cam["preferred_ip"] or nvr_ip or udp_ip or lan_ip
            want_mac = expected_nvr_mac(cam)

            issues = []
            needs_nvr_update = False

            if not nvr_enabled or nvr_status == "NoConfig":
                issues.append("Canal desativado/NoConfig no NVR")
                needs_nvr_update = True

            if best_ip and nvr_ip != best_ip:
                issues.append(f"IP divergente no NVR ({nvr_ip or '-'} -> {best_ip})")
                needs_nvr_update = True

            if nvr_user_cfg != cam["user"] or nvr_pass_cfg != cam["password"]:
                issues.append("Credenciais divergentes no NVR")
                needs_nvr_update = True

            if nvr_mac.lower() != want_mac.lower():
                if want_mac == "":
                    issues.append(f"MacAddr ({nvr_mac}) causaria conflito UDP 1532 -> limpar")
                else:
                    issues.append(f"Vincular MacAddr ({want_mac}) p/ auto-tracking")
                needs_nvr_update = True

            if best_probe["ok"]:
                health_str = f"🟢 OK ({best_probe['latency_ms']} ms)"
            elif best_probe["locked_206"]:
                health_str = "🔒 Ret=206 (Lock)"
                issues.append("Conta bloqueada temporariamente (30m)")
            else:
                health_str = "🔴 Sem resposta"
                if not issues:
                    issues.append("Aguardando reconexão Wi-Fi/energia")

            diag_str = "; ".join(issues) if issues else "✅ Saudável"

            if needs_nvr_update and apply_heal and target_ip:
                rem_devs[idx] = build_decoder_entry(cam, target_ip, rem if rem.get("Decoder") else None)
                rem_modified = True
                action_msg = f"[{code}] Self-Heal NVR: IP={target_ip}, User={cam['user']}, MacAddr={want_mac!r} ({diag_str})"
                actions_taken.append(action_msg)
                diag_str = f"🔧 CURADO -> {target_ip}" if not dry_run else f"🔍 [DRY-RUN] Curar -> {target_ip}"

            print(
                f"{code:<5} | {nvr_status:<10} | { (nvr_ip or '-'):<14} | { (lan_ip or '-'):<14} | "
                f"{ (udp_ip or '-'):<14} | {health_str:<18} | {diag_str}"
            )

            report_rows.append({
                "code": code,
                "nvr_status": nvr_status,
                "nvr_ip": nvr_ip,
                "lan_ip": lan_ip,
                "udp_ip": udp_ip,
                "reachable_ip": best_ip,
                "healthy": best_probe["ok"],
                "latency_ms": best_probe["latency_ms"],
                "locked_206": best_probe["locked_206"],
                "issues": issues,
            })

        if rem_modified and apply_heal and not dry_run:
            _, set_res = nvr.request(
                1040,
                {
                    "Name": "NetWork.RemoteDeviceV3",
                    "NetWork.RemoteDeviceV3": rem_devs,
                    "SessionID": nvr.session_hex,
                },
            )
            print(f"\n✅ [SELF-HEAL] Configuração gravada no NVR ({nvr_host}): Ret={set_res.get('Ret')}")
            for act in actions_taken:
                print(f"   -> {act}")
        elif rem_modified and dry_run:
            print("\n🔍 [DRY-RUN] Ações de Self-Heal simuladas (nenhuma escrita enviada ao NVR):")
            for act in actions_taken:
                print(f"   -> {act}")

        return {
            "timestamp": now_str,
            "channels": report_rows,
            "actions_taken": actions_taken,
            "healed": rem_modified and apply_heal and not dry_run,
        }
    finally:
        nvr.close()


def main():
    parser = argparse.ArgumentParser(
        description="Monitor de Saúde e Self-Healing de Câmeras IP (NVR XiongMai + LanSentry)"
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="check",
        choices=["check", "heal"],
        help="'check' apenas diagnostica (padrão); 'heal' corrige automaticamente divergências no NVR",
    )
    parser.add_argument("--nvr-host", default=DEFAULT_NVR_HOST, help="IP do NVR (padrão: 192.168.1.20)")
    parser.add_argument("--nvr-port", type=int, default=DEFAULT_NVR_PORT, help="Porta DVRIP do NVR (padrão: 34567)")
    parser.add_argument("--nvr-user", default=DEFAULT_NVR_USER, help="Usuário do NVR")
    parser.add_argument("--nvr-pass", default=DEFAULT_NVR_PASS, help="Senha do NVR")
    parser.add_argument("--lansentry-url", default=DEFAULT_LANSENTRY_URL, help="URL da API do LanSentry")
    parser.add_argument("--dry-run", action="store_true", help="Simula o self-healing sem gravar no NVR")
    parser.add_argument("--json", action="store_true", help="Imprime o relatório final também em JSON")

    args = parser.parse_args()
    res = evaluate_and_heal(
        nvr_host=args.nvr_host,
        nvr_port=args.nvr_port,
        nvr_user=args.nvr_user,
        nvr_pass=args.nvr_pass,
        lansentry_url=args.lansentry_url,
        apply_heal=(args.mode == "heal"),
        dry_run=args.dry_run,
    )
    if args.json:
        print("\n" + json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
