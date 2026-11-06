---
name: nvr_xiongmai
description: Guia operacional, protocolo binário DVRIP (Sofia NetSDK porta 34567), RTSP Digest (554), catálogo de canais/câmeras e monitoramento de eventos de Detecção Humana por IA embarcada para o NVR XiongMai NBD88X09S-KL (192.168.1.20).
---

# Skill: NVR XiongMai & Câmeras IP com IA Humana (`nvr_xiongmai`)

Esta skill documenta a arquitetura, credenciais, protocolos e ferramentas de inspeção/automação do **NVR Linux Embarcado XiongMai (`NBD88X09S-KL`)** em `192.168.1.20` e suas câmeras IP na LAN.

---

## 🖥️ 1. Identidade do Equipamento (NVR)

* **IP Estático (LAN):** `192.168.1.20`
* **MAC Address:** `00:12:43:24:4e:c6`
* **Placa / Hardware (`HardWare`):** `NBD88X09S-KL` (HVR/NVR de 9 canais digitais até 4K)
* **Versão de Firmware:** `V4.03.R11.C6380235.12201.140000.0000000` (Build `2021-11-19`)
* **Serial Number:** `42c180659072bbeajcp1`
* **Credenciais Administrativas:**
  * **Usuário:** `brunoconter`
  * **Senha:** `blurbang` (Hash `xm_md5`: `k2l7isVj`)
  * *(Nota: o usuário `admin` retorna `Ret: 205` — desativado/bloqueado; utilize sempre `brunoconter`).*
* **Portas TCP Abertas:**
  * `80/tcp`: Web Viewer HTTP (`RSUI` / `pluginVersion.js` com `g_b8M = true`)
  * `554/tcp`: Servidor RTSP (`H264DVR 1.0`, autenticação HTTP Digest)
  * `30100/tcp`: Porta auxiliar de transporte
  * `34567/tcp`: Protocolo binário nativo **DVRIP (Sofia NetSDK)** sobre TCP

---

## 📹 2. Catálogo dos 9 Canais (`NetWork.RemoteDeviceV3`)

| Canal | Índice DVRIP | Status no NVR | IP Configurado no NVR | IP Real na LAN (MAC) | SoC / Modelo da Câmera | Protocolo | Usuário / Senha da Câmera | IA Humana (`Detect.HumanDetection`) |
| :--- | :---: | :---: | :---: | :--- | :--- | :---: | :--- | :--- |
| **D01** | `0` | `Offline` | `192.168.1.3` | Offline (`d4:a3:eb:89:bd:f4`) | Shenzhen iComm | TCP `34567` | `kxhu` / `7prkra` | — |
| **D02** | `1` | `Offline` | `192.168.1.11` | Offline (`c4:3c:b0:79:80:db`) | Shenzhen Bilian | ONVIF `5000` | `admin` / `12345678abc` | — |
| **D03** | `2` | **`Connected`** (`1080P`) | `192.168.1.31` | **`192.168.1.31`** (`00:13:00:01:61:7b`) | `XM530V200_IPG-X2-WQ-BL_8M` | TCP `34567` | `usma` / `n2ykyy` | **Ativa** (`Sensitivity: 1`, polígono 5 pts) |
| **D04** | `3` | **`Connected`** (`4MP`) | `192.168.1.11` | **`192.168.1.11`** (`38:be:ab:91:96:85`) | `IPC_GK7202V300_G4-WR_S38` | TCP `34567` | `admin` / `23blurbang86` | **Ativa** (`Sensitivity: 1`, polígono 4 pts) |
| **D05** | `4` | `Offline` | `192.168.1.1` | `192.168.1.2` (`48:8f:4c:3d:13:14`) | Shenzhen Trolink | ONVIF `5000` | `admin` / `23blurbang86` | — |
| **D06** | `5` | `Offline` | `192.168.1.2` | `192.168.1.9` (`a4:ef:15:30:79:32`) | `IPC_GK7202V300_G4-WR_S38` (*"vizinho"*) | TCP `34567` | `admin` / `23blurbang` | **Ativa** (`Sensitivity: 1`, polígono 5 pts) |
| **D07..D09** | `6..8` | `NoConfig` | — | — | — | — | — | — |

---

## 🔐 3. Especificação Técnica do Protocolo DVRIP (`34567/tcp`)

### 3.1 Cabeçalho Binário (20 Bytes Little-Endian)
Todo pacote enviado ou recebido na porta `34567/tcp` possui um cabeçalho de 20 bytes (`struct.pack("<BB2xII2xHI", 0xff, 0x00, session_id, seq_num, msg_id, len(body))`) seguido pelo JSON terminado em `\x0a\x00`:

| Offset | Tipo | Valor / Descrição |
| :---: | :---: | :--- |
| `0` | `uint8` | `0xFF` (Magic Byte) |
| `1` | `uint8` | `0x00` ou `0x01` (Versão) |
| `2..3` | `2x` | Reservado (`0x00 0x00`) |
| `4..7` | `uint32` | `session_id` (`0` antes do login) |
| `8..11` | `uint32` | `seq_num` (contador sequencial) |
| `12..13` | `2x` | Total de pacotes / pacote atual (`0x00 0x00`) |
| `14..15` | `uint16` | `msg_id` (ID do comando DVRIP) |
| `16..19` | `uint32` | Tamanho em bytes do payload JSON + `\x0a\x00` |

### 3.2 Algoritmo de Hash de Senha (`xm_md5`)
O campo `"PassWord"` no login (`msg_id = 1000`, `"EncryptType": "MD5"`) utiliza o hash de 8 caracteres em base62 derivado do MD5:

```python
import hashlib

def xm_md5(password: str) -> str:
    d = hashlib.md5(password.encode("utf-8")).digest()
    out = []
    for i in range(8):
        v = (d[2 * i] + d[2 * i + 1]) % 62
        if v < 10:
            out.append(chr(48 + v))       # '0'..'9'
        elif v < 36:
            out.append(chr(55 + v))       # 'A'..'Z'
        else:
            out.append(chr(61 + v))       # 'a'..'z'
    return "".join(out)
```

### 3.3 Principais `msg_id` Suportados (Somente Leitura)
* `1000` $\rightarrow$ `1001`: **Login** (`{"EncryptType": "MD5", "LoginType": "DVRIP-Web", "PassWord": xm_md5(pwd), "UserName": user}`)
* `1006` $\rightarrow$ `1007`: **KeepAlive** (`{"Name": "KeepAlive", "SessionID": sess_hex}`) — enviar a cada 15-20s (`AliveInterval = 21`).
* `1020` $\rightarrow$ `1021`: **SystemInfo** (`{"Name": "SystemInfo", "SessionID": sess_hex}`)
* `1042` $\rightarrow$ `1043`: **OPSystemConfig (GetConfig)** — Principais chaves `"Name"`:
  * `"NetWork.ChnStatus"`: Status e resolução atual dos canais `D01..D09`.
  * `"NetWork.RemoteDeviceV3"`: Tabela de câmeras IP vinculadas aos canais.
  * `"Detect.HumanDetection.[0..8]"`: Configuração de IA Humana, sensibilidade e polígonos `PedRule`.
  * `"Detect.MotionDetect.[0..8]"`: Configuração de detecção de movimento.
* `1360` $\rightarrow$ `1361`: **SystemFunction** (`{"Name": "SystemFunction", "SessionID": sess_hex}`)
* `1452` $\rightarrow$ `1453`: **OPTimeQuery** (`{"Name": "OPTimeQuery", "SessionID": sess_hex}`)
* `1500` $\rightarrow$ `1501`: **GuardReq (Assinatura de Eventos Push)** (`{"SessionID": sess_hex}`)
* `1504` (Push assíncrono do NVR/Câmera): **AlarmInfo**
  ```json
  {
    "AlarmInfo": {
      "Channel": 2,
      "Event": "MotionDetect",
      "StartTime": "2026-11-05 21:00:00",
      "Status": "Start"
    },
    "Name": "AlarmInfo",
    "SessionID": "0x0000001f"
  }
  ```
  *Nota sobre Alta Confiança:* Nas câmeras com `"MotionHumanDection": true` e `"Detect.HumanDetection.[n].Enable": true` (**D03** e **D04**), o chip de IA filtra os eventos em hardware para que `AlarmInfo` dispare apenas quando um humano é reconhecido dentro da região `PedRule`.

---

## 🎥 4. Fluxos RTSP (`554/tcp` com HTTP Digest Auth)

O servidor `H264DVR 1.0` na porta `554/tcp` exige autenticação **RTSP Digest**:
* **MainStream (Alta Resolução - Canal $N \in [1..9]$):**
  `rtsp://brunoconter:blurbang@192.168.1.20:554/user=brunoconter&password=blurbang&channel=3&stream=0.sdp`
* **SubStream (Extra Stream leve - Canal $N \in [1..9]$):**
  `rtsp://brunoconter:blurbang@192.168.1.20:554/user=brunoconter&password=blurbang&channel=3&stream=1.sdp`

---

## 🛠️ 5. Utilitário CLI (`scripts/nvr_tool.py`)

O repositório inclui a ferramenta somente-leitura `scripts/nvr_tool.py` (sem dependências externas):

```bash
# 1. Status geral do NVR, relógio interno e tabela dos 9 canais
python3 scripts/nvr_tool.py status

# 2. Inspecionar configuração de Detecção Humana (IA e polígonos PedRule)
python3 scripts/nvr_tool.py human-config

# 3. Monitorar em tempo real no terminal os eventos de detecção de pessoas (Guard 1500 -> AlarmInfo 1504)
python3 scripts/nvr_tool.py listen
```
