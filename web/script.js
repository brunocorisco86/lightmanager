async function fetchData(endpoint) {
    const response = await fetch(`/api/${endpoint}`);
    if (!response.ok) throw new Error(`Erro ao buscar ${endpoint}`);
    return await response.json();
}

async function sendCommand(topic, action) {
    try {
        await fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, action })
        });
        // Feedback visual imediato
        setTimeout(updateStatus, 800);
    } catch (e) {
        alert("Erro ao enviar comando");
    }
}

async function updateSunInfo() {
    try {
        const sun = await fetchData('sun');
        // Converter ISO UTC para Objeto Date Local
        const sunriseDate = new Date(sun.sunrise);
        const sunsetDate = new Date(sun.sunset);
        
        const options = { hour: '2-digit', minute: '2-digit' };
        const sunrise = sunriseDate.toLocaleTimeString('pt-BR', options);
        const sunset = sunsetDate.toLocaleTimeString('pt-BR', options);
        
        document.getElementById('sun-info').innerHTML = `
            🌅 Aurora: <b>${sunrise}</b> | 🌇 Pôr do sol: <b>${sunset}</b>
        `;
    } catch (e) {
        document.getElementById('sun-info').innerText = "Erro ao carregar dados do sol.";
    }
}

async function updateStatus() {
    try {
        const status = await fetchData('status');
        const container = document.getElementById('light-cards');
        container.innerHTML = '';

        status.forEach(light => {
            const card = document.createElement('div');
            card.className = 'card';
            const isON = light.state === 'ON';
            
            card.innerHTML = `
                <h3>${light.name}</h3>
                <span class="status-badge ${isON ? 'status-on' : 'status-off'}">
                    ${light.state}
                </span>
                <div class="btn-group">
                    <button class="btn-on" onclick="sendCommand('${light.topic}', 'ON')">LIGAR</button>
                    <button class="btn-off" onclick="sendCommand('${light.topic}', 'OFF')">DESLIGAR</button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (e) {
        console.error("Erro ao atualizar status:", e);
    }
}

// Alias para o botão Refresh do HTML
function loadStatus() {
    updateStatus();
    updateSunInfo();
}

/* Modal and Tabs Logic */
function openConfigModal() {
    document.getElementById('configModal').style.display = 'block';
    loadConfigList();
}

function closeConfigModal() {
    document.getElementById('configModal').style.display = 'none';
}

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    
    document.getElementById(`tab-${tabName}`).classList.add('active');
    event.currentTarget.classList.add('active');
    
    if (tabName === 'solar') loadSolarHistory();
    if (tabName === 'manage') loadConfigList();
}

/* Config CRUD Functions */
async function loadConfigList() {
    const list = document.getElementById('config-list');
    try {
        console.log("Buscando pontos de configuração...");
        const points = await fetchData('config/points');
        console.log("Pontos recebidos:", points);
        
        if (!points || points.length === 0) {
            list.innerHTML = '<p style="color: #94a3b8;">Nenhum ponto cadastrado.</p>';
            return;
        }

        list.innerHTML = '';
        points.forEach(p => {
            const item = document.createElement('div');
            item.className = 'config-item';
            item.innerHTML = `
                <div style="margin-bottom: 5px;"><strong>${p.name}</strong></div>
                <div style="font-size: 0.8em; color: #94a3b8; margin-bottom: 10px;">${p.topic}</div>
                <div class="config-row">
                    <div>
                        Ligar: <input type="number" id="on-${p.id}" value="${p.offset_on}" style="width: 50px;"> <small>min</small>
                    </div>
                    <div>
                        Desligar: <input type="number" id="off-${p.id}" value="${p.offset_off}" style="width: 50px;"> <small>min</small>
                    </div>
                    <button class="btn-on" style="padding: 5px 12px;" onclick="saveConfig(${p.id})" title="Salvar">💾</button>
                </div>
            `;
            list.appendChild(item);
        });
    } catch (e) {
        console.error("Erro ao carregar lista de configuração:", e);
        list.innerHTML = `<p style="color: #ef4444;">Erro: ${e.message}</p>`;
    }
}

async function saveConfig(id) {
    const offset_on = document.getElementById(`on-${id}`).value;
    const offset_off = document.getElementById(`off-${id}`).value;
    
    try {
        const res = await fetch(`/api/config/points/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                offset_on_minutes: parseInt(offset_on), 
                offset_off_minutes: parseInt(offset_off) 
            })
        });
        if (res.ok) alert("✅ Configuração salva!");
        else alert("❌ Erro ao salvar.");
    } catch (e) {
        alert("❌ Erro de conexão.");
    }
}

async function createNewPoint(event) {
    event.preventDefault();
    const name = document.getElementById('new-name').value;
    const topic = document.getElementById('new-topic').value;
    const power = document.getElementById('new-power').value;
    
    try {
        const res = await fetch('/api/config/points', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, mqtt_topic: topic, power_w: parseFloat(power) })
        });
        
        if (res.ok) {
            alert("✅ Ponto cadastrado!");
            document.getElementById('new-point-form').reset();
            showTab('manage');
            updateStatus();
        } else {
            const err = await res.json();
            alert(`❌ Erro: ${err.detail}`);
        }
    } catch (e) {
        alert("❌ Erro ao cadastrar.");
    }
}

async function loadSolarHistory() {
    const body = document.getElementById('solar-history-body');
    try {
        console.log("Buscando histórico solar...");
        body.innerHTML = '<tr><td colspan="3">Carregando...</td></tr>';
        const history = await fetchData('config/solar_history');
        console.log("Histórico solar recebido:", history);
        
        body.innerHTML = '';
        if (!history || history.length === 0) {
            body.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #94a3b8;">Nenhum registro.</td></tr>';
            return;
        }
        
        history.forEach(h => {
            const date = new Date(h.timestamp);
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${date.toLocaleString('pt-BR')}</td>
                <td>${h.name}</td>
                <td style="color: ${h.event === 'ON' ? '#34d399' : '#f87171'}; font-weight: bold;">${h.event}</td>
            `;
            body.appendChild(row);
        });
    } catch (e) {
        console.error("Erro ao carregar histórico solar:", e);
        body.innerHTML = `<tr><td colspan="3" style="color: #ef4444;">Erro: ${e.message}</td></tr>`;
    }
}

// Fechar modal ao clicar fora
window.onclick = function(event) {
    const modal = document.getElementById('configModal');
    if (event.target == modal) closeConfigModal();
}

async function loadChart() {
    try {
        const history = await fetchData('history');
        if (history.length === 0) return;

        const ctx = document.getElementById('usageChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: history.map(h => h.date),
                datasets: [{
                    label: 'Horas Ligadas',
                    data: history.map(h => h.hours),
                    backgroundColor: '#38bdf8',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, grid: { color: '#334155' }, ticks: { color: '#f8fafc' } },
                    x: { grid: { display: false }, ticks: { color: '#f8fafc' } }
                },
                plugins: {
                    legend: { labels: { color: '#f8fafc' } }
                }
            }
        });
    } catch (e) {
        console.error("Erro ao carregar gráfico:", e);
    }
}

// Inicialização
updateSunInfo();
updateStatus();
loadChart();

// Polling suave
setInterval(updateStatus, 5000);
