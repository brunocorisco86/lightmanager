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
