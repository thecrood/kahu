// Function to toggle theme
function toggleTheme() {
  const themeButtonIcon = document.querySelector('.theme-button i');
  document.body.classList.toggle('dark-theme');

  if (document.body.classList.contains('dark-theme')) {
    themeButtonIcon.classList.remove('fa-moon');
    themeButtonIcon.classList.add('fa-sun');
  } else {
    themeButtonIcon.classList.remove('fa-sun');
    themeButtonIcon.classList.add('fa-moon');
  }
}

// Function to toggle sidebar collapse/expand
function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const botbot = document.getElementById('botbot');
  
  sidebar.classList.toggle('collapsed');

  if (sidebar.classList.contains('collapsed')) {
    sidebar.style.minWidth = '50px'; // Adjust to desired minimum width for collapsed state
    botbot.style.display = 'none';   // Hide the botbot element
  } else {
    sidebar.style.minWidth = '225px'; // Adjust to desired minimum width for expanded state
    botbot.style.display = 'block';   // Show the botbot element
  }
}


// Function to check input in message input field
function checkInput() {
  const messageInput = document.getElementById('messageInput').value.trim();
  const sendButton = document.getElementById('sendButton');
  if (messageInput !== '') {
    sendButton.disabled = false;
    sendButton.style.backgroundColor = '#000'; // Original background color
    sendButton.style.color = '#fff'; // White text
  } else {
    sendButton.disabled = true;
    sendButton.style.backgroundColor = '#222'; // Original background color
    sendButton.style.color = '#fff'; // Original text color
  }
}

// Function to store chat history in local storage
function storeChatHistory(chatHistory) {
  localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
}

// Function to retrieve chat history from local storage
function getChatHistory() {
  const chatHistory = localStorage.getItem('chatHistory');
  return chatHistory ? JSON.parse(chatHistory) : [];
}


// Function to update the sidebar with the first human question
function updateSidebarWithLastQuestion(chatId, question) {
  const previousConversations = document.getElementById('previousConversations');
  
  // Create new conversation item
  const newConversationItem = document.createElement('li');
  newConversationItem.classList.add('list-group-item');
  newConversationItem.dataset.chatId = chatId;

  // Create a wrapper div for the question text and delete button
  const wrapperDiv = document.createElement('div');
  wrapperDiv.classList.add('d-flex', 'justify-content-between', 'align-items-center');
  newConversationItem.appendChild(wrapperDiv);

  // Question text
  const questionText = document.createElement('span');
  questionText.textContent = question;
  wrapperDiv.appendChild(questionText);

  // Delete button
  const deleteButton = document.createElement('i');
  deleteButton.classList.add('fas', 'fa-trash-alt', 'delete-icon');
  deleteButton.title = 'Delete Conversation';
  deleteButton.style.visibility = 'hidden'; // Initially hidden
  wrapperDiv.appendChild(deleteButton);

  // Show delete button and blur text on hover
  newConversationItem.addEventListener('mouseenter', function () {
    deleteButton.style.visibility = 'visible';
    questionText.classList.add('blurred-text');
  });

  newConversationItem.addEventListener('mouseleave', function () {
    deleteButton.style.visibility = 'hidden';
    questionText.classList.remove('blurred-text');
  });

  // Delete conversation on button click
  deleteButton.addEventListener('click', function (event) {
    event.stopPropagation(); // Prevent the click event from bubbling up
    deleteConversation(chatId); // Delete from local storage
    newConversationItem.remove(); // Remove from sidebar
  });

  // Load conversation and highlight item on click
  newConversationItem.addEventListener('click', function () {
    // Remove active class from all conversation items
    const conversationItems = document.querySelectorAll('.list-group-item');
    conversationItems.forEach(item => {
      item.classList.remove('active');
    });

    // Add active class to the clicked conversation item
    newConversationItem.classList.add('active');

    // Load the conversation
    loadConversation(chatId);
  });

  // Prepend new conversation item to the sidebar
  const firstConversationItem = previousConversations.firstChild;
  if (firstConversationItem) {
    previousConversations.insertBefore(newConversationItem, firstConversationItem);
  } else {
    previousConversations.appendChild(newConversationItem); // If no existing items, append normally
  }

  // Highlight the newly added conversation item
  const conversationItems = document.querySelectorAll('.list-group-item');
  conversationItems.forEach(item => {
    item.classList.remove('active');
  });
  newConversationItem.classList.add('active');
}


// Function to delete a conversation from local storage
function deleteConversation(chatId) {
  let chatHistory = getChatHistory();
  chatHistory = chatHistory.filter(chat => chat.id !== chatId);
  localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
  addNewConversation();
}


// Modified sendMessage function to handle appending the first human question
async function sendMessage() {
  const messageInput = document.getElementById('messageInput');
  const sendButton = document.getElementById('sendButton');
  const messageText = messageInput.value.trim();

  if (!messageText) return;

  // Add the user's message to the chat
  appendMessage('human', messageText);

  // Store the chat history
  const chatHistory = getChatHistory();
  const currentChatId = localStorage.getItem('currentChatId');
  const currentChat = chatHistory.find(chat => chat.id === currentChatId);

  if (currentChat) {
    currentChat.messages.push({ type: 'human', text: messageText });

    // If it's the first human message in the chat, update the sidebar
    if (currentChat.messages.filter(msg => msg.type === 'human').length === 1) {
      updateSidebarWithLastQuestion(currentChatId, messageText);
    }
  } else {
    const newChatId = Date.now().toString();
    const newChat = { id: newChatId, messages: [{ type: 'human', text: messageText }] };
    chatHistory.push(newChat);
    localStorage.setItem('currentChatId', newChatId);
    updateSidebarWithLastQuestion(newChatId, messageText);
  }

  storeChatHistory(chatHistory);

  // Clear the input field and disable the send button
  messageInput.value = '';
  checkInput();

  // Add typing indicator
  showTypingIndicator();

  // Simulating a fetch request to a backend endpoint
  try {
    const response = await fetch('/al3todatabase/chatbot', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ question: messageText })
    });

    if (!response.ok) {
      appendMessage('bot', "Sorry, I cannot answer that.");
      throw new Error("Network response was not ok");
    }

    const data = await response.json();

    // Remove typing indicator and update UI with received message
    hideTypingIndicator();

    // Ensure it's a valid bot response before appending
    if (data && data.text) {
      appendMessage('bot', data.text);

      // Store the bot's response in chat history
      currentChat.messages.push({ type: 'bot', text: data.text });
      storeChatHistory(chatHistory);
    } else {
      appendMessage('bot', "Sorry, I cannot answer that.");
      throw new Error("Invalid bot response");
    }

    // Scroll to the bottom of the messages container after adding new message
    scrollToBottom();

  } catch (error) {
    console.error("Error:", error);
    // Handle errors here, such as displaying an error message to the user
    hideTypingIndicator();
    scrollToBottom();
  }
}

// Function to append message to the chat interface
function appendMessage(type, message) {
  const messagesContainer = document.getElementById('messages');
  const messageClass = type === 'bot' ? 'message bot' : 'message human';
  const iconClass = type === 'bot' ? 'icon ml-3' : 'icon mr-3';
  const iconSrc = type === 'bot' ? 'static/images/newlogo.png' : 'static/images/user.png';

  const messageElement = `
    <div class="${messageClass}">
      <div class="${iconClass}">
        <img src="${iconSrc}" alt="${type} Icon">
      </div>
      <div class="message-content">
        <div class="cpy">
          ${type === 'bot' ? '<i class="fa-regular fa-clipboard copy-btn" onclick="copyMessage(this)"></i>' : ''}
        </div>
        <div>
          ${message}
        </div>
      </div>
    </div>
  `;

  messagesContainer.innerHTML += messageElement;
}

// Function to show typing indicator
function showTypingIndicator() {
  const messagesContainer = document.getElementById('messages');
  const typingIndicator = `
    <div class="message bot typing-indicator" id="typingIndicator">
      <div class="icon ml-3">
        <img src="static/images/newlogo.png" alt="Bot Icon">
      </div>
      <div class="message-content mt-2">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;

  // Append typing indicator to messages container
  messagesContainer.innerHTML += typingIndicator;

  // Scroll to the bottom of the messages container after adding indicator
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Function to hide typing indicator
function hideTypingIndicator() {
  const typingIndicator = document.getElementById('typingIndicator');
  if (typingIndicator) {
    typingIndicator.remove();
  }
}

// Function to clear chat history and messages from the chat interface
function clearChat() {
  // Clear chat history from local storage
  localStorage.removeItem('chatHistory');

  // Clear sidebar (previous conversations)
  const previousConversations = document.getElementById('previousConversations');
  previousConversations.innerHTML = '';

  // Clear current chat interface
  const messagesContainer = document.getElementById('messages');
  messagesContainer.innerHTML = '';

  // Reset the chat interface to start a new conversation
  addNewConversation();
}


// Function to load a specific conversation from the chat history into the chat interface
function loadConversation(chatId) {
  const chatHistory = getChatHistory();
  const conversation = chatHistory.find(chat => chat.id === chatId);

  if (!conversation) return;

  // Clear current chat
  clearChatInterface();

  // Load the conversation
  conversation.messages.forEach(message => {
    appendMessage(message.type, message.text);
  });

  // Highlight the selected conversation item in the sidebar
  highlightSidebarItem(chatId);

  // Set the current chat ID in local storage
  localStorage.setItem('currentChatId', chatId);

  // Scroll to the bottom of the messages container after loading
  scrollToBottom();
}


// Function to highlight the selected conversation item in the sidebar
function highlightSidebarItem(chatId) {
  const conversationItems = document.querySelectorAll('.list-group-item');
  conversationItems.forEach(item => {
    if (item.dataset.chatId === chatId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });
}

// Function to handle key press events in the message input field
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('messageInput').addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
      sendMessage();
    }
  });

  // Load chat history from local storage
  loadChatHistory();

  // Initial bot message if chat history is empty
  const chatHistory = getChatHistory();
  if (chatHistory.length === 0) {
    appendMessage('bot', 'How can I help you today?');
    const initialChat = { id: Date.now().toString(), messages: [{ type: 'bot', text: 'How can I help you today?' }] };
    chatHistory.push(initialChat);
    storeChatHistory(chatHistory);
    localStorage.setItem('currentChatId', initialChat.id);
  }

  // Show the latest conversation on page load
  const latestChatId = localStorage.getItem('currentChatId');
  loadConversation(latestChatId);

  // Add event listener to new chat button
  const newChatButton = document.getElementById('newchat');
  newChatButton.addEventListener('click', function() {
    addNewConversation();
  });

  // Add event listener to sidebar items
  const sidebarItems = document.querySelectorAll('.previous-conversations .list-group-item');
  sidebarItems.forEach(item => {
    item.addEventListener('click', function() {
      loadConversation(this.dataset.chatId);
    });
  });
});

// Function to copy a message content to clipboard
function copyMessage(button) {
  const messageContent = button.parentElement.nextElementSibling.innerText.trim();
  navigator.clipboard.writeText(messageContent);

  // Create the "Copied!" text element
  const copiedText = document.createElement('span');
  copiedText.innerText = 'Copied!';
  copiedText.style.color = 'green';
  copiedText.style.marginRight = '10px'; // Add some space between the text and the icon
  copiedText.style.fontSize = '0.7em'; // Reduce the font size

  // Insert the "Copied!" text before the copy button
  button.parentElement.appendChild(copiedText, button);

  // Remove the "Copied!" text after 1.5 seconds
  setTimeout(() => {
    copiedText.remove();
  }, 1500);
}

// Function to add a new conversation with initial bot message
function addNewConversation() {
  // Clear the chat interface
  clearChatInterface();

  // Create a new chat with initial bot message
  const chatHistory = getChatHistory();
  const newChat = { id: Date.now().toString(), messages: [{ type: 'bot', text: 'How can I help you today?' }] };
  chatHistory.push(newChat);
  storeChatHistory(chatHistory);
  localStorage.setItem('currentChatId', newChat.id);

  // Display the initial bot message
  appendMessage('bot', 'How can I help you today?');

  // Clear the input field and disable the send button (if needed)
  checkInput();
}

// Function to clear the chat interface (UI)
function clearChatInterface() {
  const messagesContainer = document.getElementById('messages');
  messagesContainer.innerHTML = '';
}

// Function to scroll to the bottom of the messages container
function scrollToBottom() {
  const messagesContainer = document.getElementById('messages');
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


// Function to load chat history from local storage
function loadChatHistory() {
  const chatHistory = getChatHistory();
  chatHistory.forEach(chat => {
    // Find the first human message in each chat to update sidebar
    const firstHumanMessage = chat.messages.find(msg => msg.type === 'human');
    if (firstHumanMessage) {
      // Only update sidebar if there's a valid human message
      updateSidebarWithLastQuestion(chat.id, firstHumanMessage.text);
    } else if (chat.messages.length === 1 && chat.messages[0].type === 'bot' && chat.messages[0].text === 'How can I help you today?') {
      // Handle the case where the only message is the initial bot message
      // Do not update sidebar with this message
    }
  });
}