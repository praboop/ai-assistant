let threads = [];
let currentThreadId = null;

// Fetch thread labels from the backend
async function fetchThreadLabels() {
  try {
    const response = await fetch('http://localhost:8000/api/thread_labels');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    threads = data;
    populateThreadList();
  } catch (error) {
    console.error('Error fetching thread labels:', error);
  }
}

// Populate the thread list in the left panel
function populateThreadList() {
  const threadList = document.getElementById('threadList');
  threadList.innerHTML = '';

  // Group messages by parent_message_id
  const groupedThreads = threads.reduce((acc, message) => {
    const parentId = message.parent_message_id || 'No Parent ID';
    if (!acc[parentId]) {
      acc[parentId] = [];
    }
    acc[parentId].push(message);
    return acc;
  }, {});

  for (const parentId in groupedThreads) {
    const listItem = document.createElement('li');
    listItem.className = 'list-group-item';
    listItem.textContent = `Parent ID: ${parentId}`;
    listItem.addEventListener('click', () => {
      currentThreadId = parentId;
      displayThreadMessages(groupedThreads[parentId]);
    });
    threadList.appendChild(listItem);
  }
}

// Display messages of the selected thread in the right panel
function displayThreadMessages(messages) {
  const threadMessages = document.getElementById('threadMessages');
  threadMessages.innerHTML = '';

  messages.forEach((message) => {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message-container';

    const messageContent = document.createElement('p');
    messageContent.textContent = `Message ID: ${message.message_id}`;
    messageContainer.appendChild(messageContent);

    const label = document.createElement('p');
    label.textContent = `Label: ${message.label}`;
    messageContainer.appendChild(label);

    const confidence = document.createElement('p');
    confidence.textContent = `Confidence Score: ${message.confidence_score}`;
    messageContainer.appendChild(confidence);

    const solution = document.createElement('p');
    solution.textContent = `Solution Message ID: ${message.solution_message_id}`;
    messageContainer.appendChild(solution);

    threadMessages.appendChild(messageContainer);
  });
}

// Search functionality
document.getElementById('searchInput').addEventListener('input', (event) => {
  const searchTerm = event.target.value.toLowerCase();
  const filteredThreads = threads.filter((message) =>
    message.message_id.toLowerCase().includes(searchTerm) ||
    (message.label && message.label.toLowerCase().includes(searchTerm))
  );
  populateFilteredThreadList(filteredThreads);
});

// Populate filtered thread list based on search
function populateFilteredThreadList(filteredMessages) {
  const threadList = document.getElementById('threadList');
  threadList.innerHTML = '';

  // Group messages by parent_message_id
  const groupedThreads = filteredMessages.reduce((acc, message) => {
    const parentId = message.parent_message_id || 'No Parent ID';
    if (!acc[parentId]) {
      acc[parentId] = [];
    }
    acc[parentId].push(message);
    return acc;
  }, {});

  for (const parentId in groupedThreads) {
    const listItem = document.createElement('li');
    listItem.className = 'list-group-item';
    listItem.textContent = `Parent ID: ${parentId}`;
    listItem.addEventListener('click', () => {
      currentThreadId = parentId;
      displayThreadMessages(groupedThreads[parentId]);
    });
    threadList.appendChild(listItem);
  }
}

// Initialize the application
fetchThreadLabels();
