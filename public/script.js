function fetchOptionChain() {
    const expiry = document.getElementById('expiry').value;
    const token = localStorage.getItem('accessToken');
    fetch(`/option-chain?accessToken=${token}&expiryDate=${expiry}`)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('tableContainer');
            container.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        });
}

function toggleChatbot() {
    const chatbot = document.getElementById('chatbot');
    chatbot.style.display = chatbot.style.display === 'none' ? 'flex' : 'none';
}

function handleChat(e) {
    if (e.key === 'Enter') {
        const input = document.getElementById('chatInput');
        const log = document.getElementById('chatLog');
        const text = input.value;
        log.innerHTML += `<div>You: ${text}</div>`;
        input.value = '';
        // Simulated chatbot reply
        setTimeout(() => {
            log.innerHTML += `<div>Bot: I'm learning from your input: "${text}"</div>`;
        }, 500);
    }
}