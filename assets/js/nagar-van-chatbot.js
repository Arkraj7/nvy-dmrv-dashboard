/**
 * Nagar Van Assistant — local knowledge retrieval + OpenCode Zen via Apps Script.
 * Set OPENCODE_API_KEY in Apps Script Project Properties (https://opencode.ai/auth).
 * Optional: OPENCODE_MODEL (default minimax-m2.5-free). Docs: https://opencode.ai/docs/zen/
 */
const NagarVanChat = (function () {
    const STOP_WORDS = new Set([
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when',
        'where', 'who', 'can', 'do', 'does', 'did', 'i', 'me', 'my', 'you', 'your',
        'we', 'they', 'it', 'this', 'that', 'of', 'in', 'on', 'at', 'to', 'for',
        'and', 'or', 'but', 'about', 'please', 'tell', 'explain', 'give'
    ]);

    let knowledge = [];
    let apiUrl = '';
    let knowledgeUrl = 'assets/data/chatbot-knowledge.json';
    let useCloudAi = true;

    const DEFAULT_REPLY =
        'Thank you for your question! I can help with Nagar Van, DMRV, CAMPA, afforestation, reporting issues, and the public survey. Try a quick question above, or email <b>arkraj.biswas6@gmail.com</b> for specific queries.';

    function normalize(text) {
        return (text || '')
            .toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function tokenize(text) {
        return normalize(text)
            .split(' ')
            .filter(function (w) { return w.length > 1 && !STOP_WORDS.has(w); });
    }

    function scoreEntry(question, entry) {
        const qNorm = normalize(question);
        const qTokens = tokenize(question);
        let score = 0;

        (entry.keywords || []).forEach(function (phrase) {
            const p = normalize(phrase);
            if (qNorm.includes(p)) score += p.split(' ').length >= 2 ? 12 : 6;
        });

        qTokens.forEach(function (tok) {
            (entry.keywords || []).forEach(function (phrase) {
                if (normalize(phrase).includes(tok)) score += 2;
            });
        });

        return score;
    }

    function findLocalAnswer(question) {
        if (!knowledge.length) return DEFAULT_REPLY;

        let best = null;
        let bestScore = 0;

        knowledge.forEach(function (entry) {
            const s = scoreEntry(question, entry);
            if (s > bestScore) {
                bestScore = s;
                best = entry;
            }
        });

        if (best && bestScore >= 4) return best.answer; // HTML allowed in knowledge base
        return DEFAULT_REPLY;
    }

    async function loadKnowledge(url) {
        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error('Knowledge load failed');
            knowledge = await res.json();
        } catch (e) {
            console.warn('NagarVanChat: using built-in fallback', e);
            knowledge = [];
        }
    }

    async function fetchCloudAnswer(question) {
        if (!useCloudAi || !apiUrl) return null;

        const body = new URLSearchParams();
        body.append('action', 'chat');
        body.append('message', question);

        const res = await fetch(apiUrl, { method: 'POST', body: body });
        if (!res.ok) return null;

        const data = await res.json();
        if (data.success && data.reply) return data.reply;
        return null;
    }

    function formatCloudReply(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
            .replace(/\n/g, '<br>');
    }

    async function getAnswer(question) {
        try {
            const cloud = await fetchCloudAnswer(question);
            if (cloud) return formatCloudReply(cloud);
        } catch (e) {
            console.warn('NagarVanChat: cloud fallback to local', e);
        }
        return findLocalAnswer(question);
    }

    async function sendUserMessage() {
        const input = document.getElementById('aiChatInput');
        if (!input) return;

        const message = input.value.trim();
        if (!message) return;

        const messagesContainer = document.getElementById('aiChatMessages');

        const userDiv = document.createElement('div');
        userDiv.className = 'user-message';
        userDiv.textContent = message;
        messagesContainer.appendChild(userDiv);

        input.value = '';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'ai-message';
        typingDiv.innerHTML = '<span class="typing">Thinking</span>';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        const reply = await getAnswer(message);
        typingDiv.innerHTML = reply;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function sendQuickQuestion(question) {
        const input = document.getElementById('aiChatInput');
        if (input) input.value = question;
        sendUserMessage();
    }

    function handleKeyPress(e) {
        if (e.key === 'Enter') sendUserMessage();
    }

    async function init(config) {
        config = config || {};
        apiUrl = config.apiUrl || '';
        knowledgeUrl = config.knowledgeUrl || knowledgeUrl;
        useCloudAi = config.useCloudAi !== false;
        await loadKnowledge(knowledgeUrl);
    }

    return {
        init: init,
        sendUserMessage: sendUserMessage,
        sendQuickQuestion: sendQuickQuestion,
        handleKeyPress: handleKeyPress,
        findLocalAnswer: findLocalAnswer
    };
})();
