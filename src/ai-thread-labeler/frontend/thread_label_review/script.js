let threads = [];
let currentThreadId = null;
let changesMade = false;

async function fetchThreads() {
  try {
    const response = await fetch('/api/threads'); // Replace with your backend endpoint
    const data = await response.json();
    threads = data;
    loadThreads();
  } catch (error) {
    console.error('Error fetching threads:', error);
  }
}

function loadThreads() {
  const threadList = document.getElementById('threadList');
  threadList.innerHTML = '';
  threads.forEach(thread => {
    const li = document.createElement('li');
    li.classList.add('list-group-item');
    li.textContent = thread.id;
    li.onclick = () => loadThreadDetails(thread.id);
    li.id = `thread-${thread.id}`;
    threadList.appendChild(li);
  });
}

function addHighlight() {
  document.querySelectorAll('.list-group-item').forEach(thread => thread.classList.remove('highlight'));
  const selectedThread = document.getElementById(`thread-${currentThreadId}`);
  if (selectedThread) selectedThread.classList.add('highlight');
}

function loadThreadDetails(threadId) {
  currentThreadId = threadId;
  addHighlight();

  const thread = threads.find(t => t.id === threadId);
  const threadMessagesContainer = document.getElementById('threadMessages');
  threadMessagesContainer.innerHTML = '';

  thread.messages.forEach(msg => {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message-container');
    messageDiv.dataset.messageId = msg.message_id;

    const messageText = document.createElement('p');
    messageText.textContent = msg.text;
    messageDiv.appendChild(messageText);

    const labelSelect = createDropdown('label', ['question', 'answer', 'clarification'], msg.label);
    labelSelect.addEventListener('change', markAsEdited);

    const confidenceInput = createInput('confidence', msg.confidence);
    confidenceInput.addEventListener('input', markAsEdited);

    const messageControls = document.createElement('div');
    messageControls.classList.add('message-controls');
    messageControls.appendChild(labelSelect);
    messageControls.appendChild(confidenceInput);

    const errorMessage = document.createElement('div');
    errorMessage.classList.add('error-message');
    errorMessage.style.display = 'none';

    messageDiv.appendChild(messageControls);
    messageDiv.appendChild(errorMessage);

    threadMessagesContainer.appendChild(messageDiv);
  });

  document.getElementById('saveButton').style.display = 'block';
  document.getElementById('saveButton').disabled = true;
}

function createDropdown(name, options, selected) {
  const select = document.createElement('select');
  select.classList.add('form-select');
  select.name = name;
  options.forEach(option => {
    const opt = document.createElement('option');
    opt.value = option;
    opt.textContent = option;
    if (option === selected) opt.selected = true;
    select.appendChild(opt);
  });
  return select;
}

function createInput(name, value) {
  const input = document.createElement('input');
  input.classList.add('form-control');
  input.type = 'number';
  input.name = name;
  input.value = value;
  input.step = '0.01';
  input.min = '0';
  input.max = '1';
  return input;
}

function markAsEdited() {
  changesMade = true;
  document.getElementById('saveButton').disabled = !changesMade;
  validateInputs();
}

function validateInputs() {
  let allValid = true;
  const messageDivs = document.getElementById('threadMessages').getElementsByClassName('message-container');

  for (const messageDiv of messageDivs) {
    const confidenceInput = messageDiv.querySelector('input[name="confidence"]');
    const errorMessage = messageDiv.querySelector('.error-message');

    const confidenceValue = parseFloat(confidenceInput.value);
    if (isNaN(confidenceValue) || confidenceValue < 0 || confidenceValue > 1) {
      errorMessage.textContent = 'Confidence must be between 0 and 1.';
      errorMessage.style.display = 'block';
      allValid = false;
    } else {
      errorMessage.style.display = 'none';
    }
  }

  document.getElementById('saveButton').disabled = !allValid || !changesMade;
}

function saveThreadChanges() {
  const thread = threads.find(t => t.id === currentThreadId);
  console.log('Saving thread changes...');
  console.log(thread);
  // TODO: Add actual save logic via fetch POST or PUT
  changesMade = false;
  document.getElementById('saveButton').disabled = true;
}

document.getElementById('searchInput').addEventListener('input', function () {
  const searchValue = this.value.toLowerCase();
  const filteredThreads = threads.filter(thread =>
    thread.messages.some(msg =>
      msg.message_id.toLowerCase().includes(searchValue) || msg.text.toLowerCase().includes(searchValue)
    )
  );
  updateThreadList(filteredThreads);
  if (filteredThreads.length > 0) {
    currentThreadId = filteredThreads[0].id;
    addHighlight();
    loadThreadDetails(currentThreadId);
  }
});

function updateThreadList(filteredThreads) {
  const threadList = document.getElementById('threadList');
  threadList.innerHTML = '';
  filteredThreads.forEach(thread => {
    const li = document.createElement('li');
    li.classList.add('list-group-item');
    li.textContent = thread.id;
    li.onclick = () => loadThreadDetails(thread.id);
    li.id = `thread-${thread.id}`;
    threadList.appendChild(li);
  });
}

// Load initial thread data on page load
fetchThreads();
