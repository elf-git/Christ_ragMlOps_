const form = document.querySelector('#chat-form');
const input = document.querySelector('#question');
const send = document.querySelector('#send');
const messages = document.querySelector('#messages');
const conversation = document.querySelector('#conversation');
const welcome = document.querySelector('#welcome');

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function scrollDown() { conversation.scrollTop = conversation.scrollHeight; }
function addMessage(kind) { const node = element('section', `message ${kind}`); messages.append(node); scrollDown(); return node; }

async function refreshStatus() {
  try {
    const response = await fetch('/api/status');
    if (!response.ok) throw Error('Unavailable');
    const status = await response.json();
    const label = status.llm_ready ? `Local AI · ${status.passages} passages` : `Source search · ${status.passages} passages`;
    document.querySelector('#status-label').textContent = label;
    document.querySelector('#status-dot').classList.add('ready');
  } catch {
    document.querySelector('#status-label').textContent = 'Service unavailable';
  }
}

async function ask(question) {
  question = question.trim();
  if (question.length < 3 || send.disabled) return;
  welcome.hidden = true;
  input.value = '';
  input.style.height = '';
  send.disabled = true;
  const user = addMessage('user');
  user.append(element('div', 'user-bubble', question));
  const reply = addMessage('assistant');
  const head = element('div', 'answer-head');
  head.append(element('span', 'answer-icon', '✣'), element('span', '', 'STUDENT DESK'));
  reply.append(head);
  const body = element('div', 'answer-body thinking', 'Looking through the documents…');
  reply.append(body);
  try {
    const response = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question})});
    if (!response.ok) throw Error('The question could not be processed.');
    const data = await response.json();
    body.classList.remove('thinking');
    body.textContent = data.answer;
    reply.append(element('p', 'answer-meta', data.answer_mode === 'source' ? 'Direct source passage · check the PDF page for full context' : data.answer_mode === 'extractive' ? 'Source passage view · local generation model unavailable or answer unverified' : `Answered with ${data.answer_mode}`));
    if (data.sources.length) {
      reply.append(element('div', 'sources-title', 'SOURCE PAGES'));
      const list = element('div', 'sources');
      for (const source of data.sources) {
        const card = element('a', 'source');
        card.href = source.url;
        card.target = '_blank';
        card.rel = 'noopener';
        const top = element('div', 'source-top');
        top.append(element('span', '', `[${source.number}] PDF PAGE ${source.page}`), element('span', '', '↗'));
        card.append(top, element('b', '', source.title), element('small', '', source.excerpt));
        list.append(card);
      }
      reply.append(list);
    }
    const feedback = element('div', 'feedback');
    feedback.append(element('span', '', 'Was this useful?'));
    for (const [symbol, helpful] of [['Yes', true], ['No', false]]) {
      const button = element('button', '', symbol);
      button.type = 'button';
      button.addEventListener('click', async () => {
        try { await fetch('/api/feedback', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({run_id:data.run_id, helpful})}); } catch {}
        feedback.querySelectorAll('button').forEach(b => b.disabled = true);
        feedback.firstChild.textContent = 'Thanks for the feedback.';
      });
      feedback.append(button);
    }
    reply.append(feedback);
  } catch (error) {
    body.className = 'error';
    body.textContent = `${error.message} Please try again.`;
  } finally {
    send.disabled = false;
    input.focus();
    scrollDown();
    refreshStatus();
  }
}

form.addEventListener('submit', event => {event.preventDefault(); ask(input.value);});
input.addEventListener('input', () => {input.style.height = 'auto'; input.style.height = `${Math.min(input.scrollHeight, 130)}px`;});
input.addEventListener('keydown', event => {if (event.key === 'Enter' && !event.shiftKey) {event.preventDefault(); ask(input.value);}});
document.querySelectorAll('.suggestion').forEach(button => button.addEventListener('click', () => ask(button.dataset.question)));
document.querySelector('#new-chat').addEventListener('click', () => {messages.replaceChildren(); welcome.hidden = false; input.focus(); conversation.scrollTop = 0;});
refreshStatus();
