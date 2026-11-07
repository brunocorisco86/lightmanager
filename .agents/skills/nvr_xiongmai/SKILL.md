---
name: nvr_xiongmai
description: Guia operacional, protocolo binário DVRIP (Sofia NetSDK porta 34567), RTSP Digest (554), orquestração de canais (NetWork.RemoteDeviceV3), armadilhas de MacAddr/msg_id=1532 e integração de Detecção Humana por IA com o Light Manager para o NVR XiongMai NBD88X09S-KL (192.168.1.20).
---

# Skill: NVR XiongMai `NBD88X09S-KL` (`nvr_xiongmai`)

Esta skill documenta a arquitetura, credenciais, protocolos binários DVRIP, regras de orquestração de canais e integração com o **Light Manager** do **NVR Linux Embarcado XiongMai (`NBD88X09S-KL`)** em `192.168.1.20`.

> **Nota:** Para o catálogo detalhado de cada câmera IP (`D01..D06`), senhas individuais, peculiaridades de hardware/SoC, topologia Wi-Fi e Self-Healing com LanSentry, consulte a skill dedicada **[`ip_cameras`](../ip_cameras/SKILL.md)**.

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
* **Portas TCP/UDP Abertas:**
  * `80/tcp`: Web Viewer HTTP (`RSUI` / `pluginVersion.js` com `g_b8M = true`)
  * `554/tcp`: Servidor RTSP (`H264DVR 1.0`, autenticação HTTP Digest)
  * `30100/tcp`: Porta auxiliar de transporte
  * `34567/tcp`: Protocolo binário nativo **DVRIP (Sofia NetSDK)** sobre TCP
  * `34568/udp` & `34569/udp`: Descoberta broadcast (`msg_id=1530/1531`) e modificação remota de IP (`msg_id=1532`)

---

## 🔐 2. Especificação Técnica do Protocolo DVRIP (`34567/tcp`)

### 2.1 Cabeçalho Binário (20 Bytes Little-Endian)
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

### 2.2 Algoritmo de Hash de Senha (`xm_md5`)
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

### 2.3 Principais `msg_id` Suportados no NVR
* `1000` $\rightarrow$ `1001`: **Login** (`{"EncryptType": "MD5", "LoginType": "DVRIP-Web", "PassWord": xm_md5(pwd), "UserName": user}`)
* `1006` $\rightarrow$ `1007`: **KeepAlive** (`{"Name": "KeepAlive", "SessionID": sess_hex}`) — enviar a cada 15-20s (`AliveInterval = 21`).
* `1020` $\rightarrow$ `1021`: **SystemInfo** (`{"Name": "SystemInfo", "SessionID": sess_hex}`)
* `1040` $\rightarrow$ `1041`: **OPSystemConfig (SetConfig)** — Usado pelo `scripts/camera_watchdog.py` para Self-Healing da tabela `"NetWork.RemoteDeviceV3"`.
* `1042` $\rightarrow$ `1043`: **OPSystemConfig (GetConfig)** — Principais chaves `"Name"`:
  * `"NetWork.ChnStatus"`: Status (`Connected`, `Offline`, `NoLogin`, `NoConfig`) e resolução atual dos canais `D01..D09`.
  * `"NetWork.RemoteDeviceV3"`: Tabela de câmeras IP vinculadas aos 9 canais.
  * `"Detect.HumanDetection.[0..8]"`: Configuração de IA Humana, sensibilidade e polígonos `PedRule` (faz proxy até a câmera; dá timeout se o canal estiver `Offline`).
  * `"Detect.MotionDetect.[0..8]"`: Configuração de detecção de movimento.
* `1360` $\rightarrow$ `1361`: **SystemFunction** (`{"Name": "SystemFunction", "SessionID": sess_hex}`)
* `1452` $\rightarrow$ `1453`: **OPTimeQuery** (`{"Name": "OPTimeQuery", "SessionID": sess_hex}`)
* `1500` $\rightarrow$ `1501`: **GuardReq (Assinatura de Eventos Push)** (`{"SessionID": sess_hex}`)
* `1504` (Push assíncrono do NVR): **AlarmInfo**
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

---

## ⚠️ 3. Regras Críticas de Orquestração de Canais (`NetWork.RemoteDeviceV3`)

O NVR possui um daemon interno de **"IP Adaptativo / Auto-Assign"** que monitora o campo `Decoder[0].MacAddr` de cada canal em `NetWork.RemoteDeviceV3`. Compreender esse comportamento evita quedas das câmeras Wi-Fi:

1. **O Perigo do `MacAddr` preenchido em Câmeras com IP Estático Secundário (`D01`, `D04` e `D06`):**
   * As câmeras `D01` (`.201`), `D04` (`.204`) e `D06` (`.206`) possuem IP estático configurado em `NetWork.NetCommon.HostIP` (`eth0`) e IP dinâmico DHCP no Wi-Fi (`wlan0`/`eth2`).
   * Se o campo `MacAddr` estiver preenchido no NVR para esses canais, o NVR detecta via broadcast UDP `1531` que o `HostIP` Wi-Fi da câmera difere do `.20x` configurado e:
     * Na `D01`: sobrescreve o `IPAddress` no NVR de volta para o IP DHCP (`.13`).
     * Na `D04` e `D06` (`IPC_GK7202V300`): dispara pacotes broadcast **`UDP msg_id=1532`** (`{"DvrMac": "00:12:43:24:4e:c6", "HostIP": "0x3901A8C0", ...}`) tentando mudar o IP da câmera para `.57`/`.58`. Isso executa `ifconfig eth0` na câmera, sobrepondo a rota `192.168.1.0/24` sobre a interface desconectada `eth0` e **derrubando a câmera do Wi-Fi**!
   * **Regra Obrigatória:** Para **`D01` (`.201`), `D04` (`.204`) e `D06` (`.206`)**, o campo `Decoder[0].MacAddr` no NVR **DEVE SEMPRE ser string vazia (`""`)**!

2. **Quando usar `MacAddr` preenchido (`D02`, `D03` e `D05`):**
   * **`D02` (`IPC_XM210` V5.08):** Opera em DHCP no Wi-Fi. Deve ter `MacAddr = "00:13:00:f6:69:a0"` (o MAC interno reportado no UDP `1531`) para que o NVR acompanhe automaticamente mudanças de IP caso o roteador reinicie.
   * **`D03` (`192.168.1.203`):** Opera com IP estático único `.203` (`MacAddr = "00:13:00:01:61:7b"`).
   * **`D05` (`192.168.1.3` ONVIF):** Usa protocolo `ONVIF` na porta `5000` (`MacAddr = "48:8f:4c:3d:13:14"`).

---

## 🎥 4. Fluxos RTSP (`554/tcp` com HTTP Digest Auth)

O servidor `H264DVR 1.0` na porta `554/tcp` exige autenticação **RTSP Digest**:
* **MainStream (Alta Resolução - Canal $N \in [1..9]$):**
  `rtsp://brunoconter:blurbang@192.168.1.20:554/user=brunoconter&password=blurbang&channel=3&stream=0.sdp`
* **SubStream (Extra Stream leve - Canal $N \in [1..9]$):**
  `rtsp://brunoconter:blurbang@192.168.1.20:554/user=brunoconter&password=blurbang&channel=3&stream=1.sdp`

---

## 🛠️ 5. Ferramentas CLI (`scripts/nvr_tool.py` & `scripts/camera_watchdog.py`)

```bash
# 1. Status geral do NVR, relógio interno e tabela dos 9 canais
python3 scripts/nvr_tool.py status

# 2. Inspecionar configuração de Detecção Humana (IA e polígonos PedRule)
python3 scripts/nvr_tool.py human-config

# 3. Monitorar em tempo real os eventos de detecção de pessoas (Guard 1500 -> AlarmInfo 1504)
python3 scripts/nvr_tool.py listen

# 4. Auditoria de saúde das câmeras (NVR + LanSentry + UDP 1531 + Latência de Login)
python3 scripts/camera_watchdog.py check

# 5. Self-Healing automático dos canais no NVR (corrige IPs, credenciais e limpa MacAddr indevidos)
python3 scripts/camera_watchdog.py heal
```

---

## 💡 6. Integração com o Light Manager (`solar_worker.py` & Web Console)

1. **Arquitetura 100% via Broker MQTT (Hardware-Agnóstica):**
   * A thread `nvr_guard_worker` dentro de `scripts/solar_worker.py` mantém uma sessão `GuardReq` (`1500`) aberta em `192.168.1.20:34567` e gerencia o ciclo `ON` $\rightarrow$ `camera_hold_seconds` (padrão `120s`) $\rightarrow$ `OFF` publicando diretamente no tópico `<mqtt_topic>/set` (`QoS 1, Retain=True`).
2. **Regras de Negócio por Ponto (`light_points`):**
   * `trigger_mode = 'solar'`: Liga no pôr do sol e desliga no nascer do sol (**Frente** e **Fundos**).
   * `trigger_mode = 'camera'`: Acionado quando qualquer canal listado em `camera_channels` (ex.: `'3,4'` para `D03` e `D04`) envia `AlarmInfo` (`Status == "Start"`), permanecendo ligado por `camera_hold_seconds` segundos (**Muro** em `home/outdoor/muro`).
   * `trigger_mode = 'manual'`: Somente acionamento manual.
3. **Observabilidade de Baixa Pegada:**
   * **Debounce de 15s por canal (`NVR_DEBOUNCE_SECONDS = 15`):** Agrupa rajadas da mesma caminhada em 1 único registro na tabela `nvr_detections` e em `logs/nvr.log`, renovando normalmente o timer da lâmpada.
   * **Silêncio no Telegram/ntfy para Câmeras:** Detecções humanas do NVR **NUNCA** enviam mensagens no Bot do Telegram ou ntfy. Apenas gatilhos do **Ciclo Solar** (`solar_trigger`) enviam notificações no Telegram.
