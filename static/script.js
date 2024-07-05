const chatInput = document.querySelector("#chat-input");
const sendButton = document.querySelector("#send-btn");
const chatContainer = document.querySelector(".chat-container");
const themeButton = document.querySelector("#theme-btn");
const deleteButton = document.querySelector("#delete-btn");
const header = document.querySelector(".header");
var typingContainer = document.querySelector('.typing-container');
var incomingChatElements = document.querySelectorAll('.chat.incoming');
var winsurtechlogo = document.querySelector('#winlogo');
// para_list = chatContainer.querySelectorAll('div > p')

let userText = null;

const loadDataFromLocalstorage = () => {
    // Load saved chats and theme from local storage and apply/add on the page
    const themeColor = localStorage.getItem("themeColor");

    document.body.classList.toggle("light-mode", themeColor === "light_mode");
    themeButton.innerText = document.body.classList.contains("light-mode") ? "dark_mode" : "light_mode";
    
    var element = document.querySelector(".header-right")
    if (themeButton.innerText ==  "light_mode") {
        element.style.color = "white";
        winsurtechlogo.src = 'static/images/logo_win1.png'
    }
    else {
        element.style.color = "black";
        winsurtechlogo.src = 'static/images/logo_win2.png'
    }

    const defaultText = `<div class="default-text">
                            <h1>WinsurtechAI</h1>
                            <p>Start a conversation and explore the power of AI.<br> Your chat history will be displayed here.</p>
                        </div>`

    chatContainer.innerHTML = localStorage.getItem("all-chats") || defaultText;
    chatContainer.scrollTo(0, chatContainer.scrollHeight); // Scroll to bottom of the chat container
}

const createChatElement = (content, className) => {
    // Create new div and apply chat, specified class and set html content of div
    const chatDiv = document.createElement("div");
    chatDiv.classList.add("chat", className);
    chatDiv.innerHTML = content;
    return chatDiv; // Return the created chat div
}

const getChatResponse = async (incomingChatDiv) => {
    // const API_URL = "/api/chat";
    const pElement = document.createElement("p");

    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    const raw = JSON.stringify({
        "question": userText
      });

    const requestOptions = {
        method: "POST",
        headers: myHeaders,
        body: raw,
        redirect: "follow"
      };

    fetch("/al3todb/chatbot", requestOptions)
    .then((response) => {
        if (!response.ok) {
            throw new Error("Network response was not ok");
        }
        return response.text();
    })
    .then((result) => {
        // Update DOM with result
        let parsedResult = JSON.parse(result);
        parsedResult = JSON.parse(parsedResult)
        let formattedText = parsedResult.text;
        pElement.textContent = formattedText;
        incomingChatDiv.querySelector(".typing-animation").remove();
        sendButton.style.pointerEvents = "auto";
        incomingChatDiv.querySelector(".chat-details").appendChild(pElement);
       
        var maxChatBatches = 5;
        if (chatContainer.children.length > maxChatBatches * 2) {
            // Calculate the number of chat batches to remove
            // var batchesToRemove = chatContainer.children.length - maxChatBatches * 2;
        
            // Loop through and remove the excess chat batches
                // Remove the first chat batch (outgoing and incoming pair)
                chatContainer.removeChild(chatContainer.children[0]);
                chatContainer.removeChild(chatContainer.children[0]);
        
        }

        
        localStorage.setItem("all-chats", chatContainer.innerHTML);
        // Get all child div elements with the specified class
        var childDivs = chatContainer.getElementsByClassName("outgoing"); // Replace "yourClass" with the class of the child divs you want to select
        

        const width = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
        if (width > 768) {
        // Get the last child div
            var latestChildDiv = childDivs[childDivs.length - 1];
            // latestChildDiv.scrollIntoView();
            var offsetTop = latestChildDiv.offsetTop - header.offsetHeight;
            chatContainer.scrollTo({
                top: offsetTop,
                behavior: 'smooth' // Optional: Adds smooth scrolling effect
            });
            // chatContainer.scrollTo(0, latestChildDiv);
        }
    })
    .catch((error) => {
        // console.error(error); // Log the error
        // Update DOM with error message
        pElement.textContent = "An error occurred: " + error.message;
        incomingChatDiv.querySelector(".typing-animation").remove();
        sendButton.style.pointerEvents = "auto";
        incomingChatDiv.querySelector(".chat-details").appendChild(pElement);
    });

  
    // Remove the typing animation, append the paragraph element and save the chats to local storage
    
}

const copyResponse = (copyBtn) => {
    // Copy the text content of the response to the clipboard
    const reponseTextElement = copyBtn.parentElement.querySelector("p");
    navigator.clipboard.writeText(reponseTextElement.textContent);
    copyBtn.textContent = "done";
    setTimeout(() => copyBtn.textContent = "content_copy", 1000);
}

const showTypingAnimation = () => {
    // Display the typing animation and call the getChatResponse function
    const html = `<div class="chat-content">
                    <div class="chat-details">
                        <img src="static/images/newlogo.png" alt="chatbot-img">
                        <div class="typing-animation">
                            <div class="typing-dot" style="--delay: 0.2s"></div>
                            <div class="typing-dot" style="--delay: 0.3s"></div>
                            <div class="typing-dot" style="--delay: 0.4s"></div>
                        </div>
                    </div>
                    <span onclick="copyResponse(this)" class="material-symbols-rounded">content_copy</span>
                </div>`;
    // Create an incoming chat div with typing animation and append it to chat container
    const incomingChatDiv = createChatElement(html, "incoming");
    chatContainer.appendChild(incomingChatDiv);
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
    getChatResponse(incomingChatDiv);
}

function updatePadding() {
    
    var newPadding = typingContainer.offsetHeight // Adjust as needed
    // typingContainer.style.padding = newPadding + 'px';
    if (/iPhone/i.test(navigator.userAgent)){
        // chatContainer.style.paddingBottom = newPadding + 'px';
        var isInLandscapeMode = window.matchMedia("(orientation: landscape)").matches;
        // incomingChatElements.forEach(function(chatElement) {
        if (isInLandscapeMode) {
            // newPadding = newPadding - 30
            // chatContainer.style.paddingBottom = newPadding + 'px';
            // chatContainer.style.maxHeight = '80vh'
            for (let i = 0; i < para_list.length; i++) {
                para_list[i].style.fontSize = "14px";
            }
            
        //       chatElement.style.fontSize = '20px'; // Adjust font size if not in landscape mode
        }
        else{
            newPadding = newPadding + 40
            chatContainer.style.paddingBottom = newPadding + 'px';
            for (let i = 0; i < para_list.length; i++) {
                para_list[i].style.fontSize = "16px";
            }
            // chatContainer.style.maxHeight = '60vh'
        }
        //   });
    }
    else{
        var isInLandscapeMode = window.matchMedia("(orientation: landscape)").matches;
        if (isInLandscapeMode) {
            newPadding = newPadding + 30
            chatContainer.style.paddingBottom = newPadding + 'px';
        }
    }
  }

function updatePaddingAndroid(){
    var newPadding = typingContainer.offsetHeight // Adjust as needed
    // typingContainer.style.padding = newPadding + 'px';
    if (/iPhone/i.test(navigator.userAgent)){
        var isInLandscapeMode = window.matchMedia("(orientation: landscape)").matches;
        if (isInLandscapeMode) {
            for (let i = 0; i < para_list.length; i++) {
                para_list[i].style.fontSize = "14px";
            }
        }
        else{
            for (let i = 0; i < para_list.length; i++) {
                para_list[i].style.fontSize = "16px";
            }
        }
    }
    else{
        newPadding = newPadding + 30
        chatContainer.style.paddingBottom = newPadding + 'px';
        // chatContainer.style.maxHeight = '80vh'
    }
}


const handleOutgoingChat = () => {
    chatInput.focus();
    sendButton.style.pointerEvents = "none";
    userText = chatInput.value.trim(); // Get chatInput value and remove extra spaces
    if(!userText) {
        sendButton.style.pointerEvents = "auto";
        return;
    } // If chatInput is empty return from here

    // Clear the input field and reset its height
    chatInput.value = "";
    // chatInput.style.height = `${initialInputHeight}px`;

    const html = `<div class="chat-content">
                    <div class="chat-details">
                        <img src="static/images/user.png" alt="user-img">
                        <p>${userText}</p>
                    </div>
                </div>`;

    // Create an outgoing chat div with user's message and append it to chat container
    const outgoingChatDiv = createChatElement(html, "outgoing");
    chatContainer.querySelector(".default-text")?.remove();
    chatContainer.appendChild(outgoingChatDiv);
    chatContainer.scrollTo(0, chatContainer.scrollHeight);
    updatePaddingAndroid();
    setTimeout(showTypingAnimation, 500);
}

window.addEventListener('orientationchange', function() {
    updatePadding();
  });

deleteButton.addEventListener("click", () => {
    // Remove the chats from local storage and call loadDataFromLocalstorage function
    const modal = document.createElement("div");
    modal.classList.add("delete-modal");
    modal.innerHTML = `
        <div class="delete-modal-content">
            <p>Are you sure you want to delete all the chats?</p>
            <div class="delete-modal-buttons">
                <button id="confirm-delete">Yes</button>
                <button id="cancel-delete">Cancel</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    // Event listener for confirm delete button
    const confirmButton = document.getElementById("confirm-delete");
    confirmButton.addEventListener("click", () => {
        localStorage.removeItem("all-chats");
        loadDataFromLocalstorage();
        closeModal();
        if (sendButton.style.pointerEvents == "none") {
            window.location.reload();
        }
    });

    // Event listener for cancel delete button
    const cancelButton = document.getElementById("cancel-delete");
    cancelButton.addEventListener("click", () => {
        closeModal();
    });
});

function closeModal() {
    const modal = document.querySelector(".delete-modal");
    if (modal) {
        modal.remove();
    }
}

themeButton.addEventListener("click", () => {
    // Toggle body's class for the theme mode and save the updated theme to the local storage 
    document.body.classList.toggle("light-mode");
    localStorage.setItem("themeColor", themeButton.innerText);
    themeButton.innerText = document.body.classList.contains("light-mode") ? "dark_mode" : "light_mode";
    var element = document.querySelector(".header-right")
    if (themeButton.innerText ==  "light_mode") {
        element.style.color = "white";
        winsurtechlogo.src = 'static/images/logo_win1.png'
    }
    else {
        element.style.color = "black";
        winsurtechlogo.src = 'static/images/logo_win2.png'
    }
});

const initialInputHeight = chatInput.scrollHeight;

// chatInput.addEventListener("input", () => {   
//     // Adjust the height of the input field dynamically based on its content
//     chatInput.style.height =  `${initialInputHeight}px`;
//     chatInput.style.height = `${chatInput.scrollHeight}px`;
// });


chatInput.addEventListener("keydown", (e) => {
    // If the Enter key is pressed without Shift and the window width is larger 
    // than 800 pixels, handle the outgoing chat
    if (sendButton.style.pointerEvents != "none"){
        if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
            e.preventDefault();
            handleOutgoingChat();
        }
    }
});

loadDataFromLocalstorage();
sendButton.addEventListener("click", handleOutgoingChat);

// document.addEventListener("click", function(event) {
//     // Check if the touch event did not originate from the input field
//     if (event.target !== chatInput && !chatInput.contains(event.target)) {
//         chatInput.blur(); // Blur the input field to hide the keyboard
//     }
// });