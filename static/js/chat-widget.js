// Chat Widget Implementation
function initializeChatWidget(settings) {
    // Default settings
    const defaultSettings = {
        theme: 'light',
        primary_color: '#060dcf',
        secondary_color: '#e3e7ee',
        chatbot_name: 'DentalBot',
        welcome_message: 'Welcome to Clinical bot! How can I assist you today?',
        bot_avatar: '/static/img/botAvatar.png',
        user_avatar: '/static/img/userAvatar.jpg',
        widget_width: '350px',
        widget_height: '500px',
        position: 'right',
        show_timestamp: true,
        enable_voice: false,
        enable_attachments: false,
        baseUrl: window.location.origin,
        apiEndpoint: '/api/chat',
        userId: null
    };

    // Merge default settings with provided settings
    settings = { ...defaultSettings, ...settings };

    // Create widget container
    const widgetContainer = document.createElement('div');
    widgetContainer.id = 'dental-chatbot-widget';
    widgetContainer.style.position = 'fixed';
    widgetContainer.style.bottom = '20px';
    widgetContainer.style[settings.position] = '20px';
    widgetContainer.style.zIndex = '1000';

    // Create widget button
    const widgetButton = document.createElement('div');
    widgetButton.id = 'widget-trigger';
    widgetButton.style.width = '60px';
    widgetButton.style.height = '60px';
    widgetButton.style.borderRadius = '50%';
    widgetButton.style.backgroundColor = settings.primary_color;
    widgetButton.style.cursor = 'pointer';
    widgetButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    widgetButton.style.display = 'flex';
    widgetButton.style.alignItems = 'center';
    widgetButton.style.justifyContent = 'center';

    // Create chat icon
    const chatIcon = document.createElement('img');
    chatIcon.src = settings.bot_avatar;
    chatIcon.style.width = '40px';
    chatIcon.style.height = '40px';
    chatIcon.style.borderRadius = '50%';
    widgetButton.appendChild(chatIcon);

    // Create chat window
    const chatWindow = document.createElement('div');
    chatWindow.id = 'chat-window';
    chatWindow.style.display = 'none';
    chatWindow.style.position = 'fixed';
    chatWindow.style.bottom = '90px';
    chatWindow.style[settings.position] = '20px';
    chatWindow.style.width = settings.widget_width;
    chatWindow.style.height = settings.widget_height;
    chatWindow.style.backgroundColor = settings.theme === 'dark' ? '#2f3136' : '#fff';
    chatWindow.style.borderRadius = '10px';
    chatWindow.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    chatWindow.style.overflow = 'hidden';
    chatWindow.style.flexDirection = 'column';
    chatWindow.style.zIndex = '1000';

    // Create chat header
    const chatHeader = document.createElement('div');
    chatHeader.style.backgroundColor = settings.primary_color;
    chatHeader.style.color = '#fff';
    chatHeader.style.padding = '15px';
    chatHeader.style.display = 'flex';
    chatHeader.style.alignItems = 'center';
    chatHeader.style.gap = '10px';

    const botAvatar = document.createElement('img');
    botAvatar.src = settings.bot_avatar;
    botAvatar.style.width = '30px';
    botAvatar.style.height = '30px';
    botAvatar.style.borderRadius = '50%';

    const botName = document.createElement('div');
    botName.textContent = settings.chatbot_name;
    botName.style.flex = '1';

    const closeButton = document.createElement('button');
    closeButton.innerHTML = '&times;';
    closeButton.style.background = 'none';
    closeButton.style.border = 'none';
    closeButton.style.color = '#fff';
    closeButton.style.fontSize = '24px';
    closeButton.style.cursor = 'pointer';

    chatHeader.appendChild(botAvatar);
    chatHeader.appendChild(botName);
    chatHeader.appendChild(closeButton);

    // Create chat messages container
    const chatMessages = document.createElement('div');
    chatMessages.id = 'chats';
    chatMessages.style.flex = '1';
    chatMessages.style.overflowY = 'auto';
    chatMessages.style.padding = '15px';
    chatMessages.style.backgroundColor = settings.secondary_color;
    chatMessages.style.color = settings.theme === 'dark' ? '#fff' : '#000';

    // Create input area
    const inputArea = document.createElement('div');
    inputArea.style.padding = '15px';
    inputArea.style.borderTop = '1px solid ' + (settings.theme === 'dark' ? '#40444b' : '#eee');
    inputArea.style.display = 'flex';
    inputArea.style.gap = '10px';
    inputArea.style.backgroundColor = settings.theme === 'dark' ? '#2f3136' : '#fff';

    const textInput = document.createElement('input');
    textInput.type = 'text';
    textInput.className = 'usrInput';
    textInput.placeholder = 'Type a message...';
    textInput.style.flex = '1';
    textInput.style.padding = '8px';
    textInput.style.border = '1px solid ' + (settings.theme === 'dark' ? '#40444b' : '#ddd');
    textInput.style.borderRadius = '20px';
    textInput.style.outline = 'none';
    textInput.style.backgroundColor = settings.theme === 'dark' ? '#40444b' : '#fff';
    textInput.style.color = settings.theme === 'dark' ? '#fff' : '#000';

    const inputControls = document.createElement('div');
    inputControls.style.display = 'flex';
    inputControls.style.gap = '5px';

    // Add attachment button if enabled
    if (settings.enable_attachments) {
        const attachButton = document.createElement('button');
        attachButton.innerHTML = '&#128206;';
        attachButton.style.background = settings.primary_color;
        attachButton.style.color = '#fff';
        attachButton.style.border = 'none';
        attachButton.style.borderRadius = '50%';
        attachButton.style.width = '35px';
        attachButton.style.height = '35px';
        attachButton.style.cursor = 'pointer';
        inputControls.appendChild(attachButton);

        // Add attachment functionality
        attachButton.addEventListener('click', () => {
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.pdf,.doc,.docx,.txt';
            fileInput.style.display = 'none';
            document.body.appendChild(fileInput);
            
            fileInput.click();
            fileInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    try {
                        const response = await fetch(`${settings.baseUrl}/files/upload`, {
                            method: 'POST',
                            body: formData
                        });
                        const data = await response.json();
                        textInput.value = `[File: ${file.name}](${data.url})`;
                    } catch (error) {
                        console.error('Error uploading file:', error);
                    }
                }
                document.body.removeChild(fileInput);
            });
        });
    }

    // Add voice input button if enabled
    if (settings.enable_voice) {
        const voiceButton = document.createElement('button');
        voiceButton.innerHTML = '&#127908;';
        voiceButton.style.background = settings.primary_color;
        voiceButton.style.color = '#fff';
        voiceButton.style.border = 'none';
        voiceButton.style.borderRadius = '50%';
        voiceButton.style.width = '35px';
        voiceButton.style.height = '35px';
        voiceButton.style.cursor = 'pointer';
        inputControls.appendChild(voiceButton);

        // Add voice recognition functionality
        let isRecording = false;
        let recognition = null;
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                textInput.value = text;
            };

            voiceButton.addEventListener('click', () => {
                if (!isRecording) {
                    recognition.start();
                    voiceButton.style.backgroundColor = '#ff4444';
                } else {
                    recognition.stop();
                    voiceButton.style.backgroundColor = settings.primary_color;
                }
                isRecording = !isRecording;
            });
        }
    }

    const sendButton = document.createElement('button');
    sendButton.innerHTML = '&#10148;';
    sendButton.style.background = settings.primary_color;
    sendButton.style.color = '#fff';
    sendButton.style.border = 'none';
    sendButton.style.borderRadius = '50%';
    sendButton.style.width = '35px';
    sendButton.style.height = '35px';
    sendButton.style.cursor = 'pointer';
    inputControls.appendChild(sendButton);

    inputArea.appendChild(textInput);
    inputArea.appendChild(inputControls);

    // Assemble chat window
    chatWindow.appendChild(chatHeader);
    chatWindow.appendChild(chatMessages);
    chatWindow.appendChild(inputArea);

    // Add components to widget container
    widgetContainer.appendChild(widgetButton);
    widgetContainer.appendChild(chatWindow);

    // Add widget to page
    document.body.appendChild(widgetContainer);

    // Helper function to format timestamp
    const formatTimestamp = () => {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Event listeners
    widgetButton.addEventListener('click', () => {
        chatWindow.style.display = chatWindow.style.display === 'none' ? 'flex' : 'none';
        if (chatWindow.style.display === 'flex' && !chatWindow.hasMessage) {
            // Add welcome message
            const welcomeMessage = document.createElement('div');
            let messageHTML = `<img class="botAvatar" src="${settings.bot_avatar}" style="width:30px;height:30px;border-radius:50%;margin-right:10px;">
                             <div class="botMsg" style="background:${settings.theme === 'dark' ? '#40444b' : 'white'};
                                                      color:${settings.theme === 'dark' ? '#fff' : '#000'};
                                                      padding:10px;border-radius:10px;max-width:80%;margin-bottom:10px;">
                                ${settings.welcome_message}
                             </div>`;
            
            if (settings.show_timestamp) {
                messageHTML += `<div class="timestamp" style="font-size:0.8em;color:#888;margin-top:2px">
                                ${formatTimestamp()}
                              </div>`;
            }
            
            welcomeMessage.innerHTML = messageHTML;
            chatMessages.appendChild(welcomeMessage);
            chatWindow.hasMessage = true;
        }
    });

    closeButton.addEventListener('click', (e) => {
        e.stopPropagation();
        chatWindow.style.display = 'none';
    });

    // Handle sending messages
    const sendMessage = () => {
        const message = textInput.value.trim();
        if (message) {
            // Add user message to chat
            const userMsgDiv = document.createElement('div');
            userMsgDiv.style.textAlign = 'right';
            userMsgDiv.style.marginBottom = '10px';

            let messageHTML = `<div class="userMsg" style="background:${settings.primary_color};
                                                         color:white;
                                                         padding:10px;
                                                         border-radius:10px;
                                                         display:inline-block;
                                                         max-width:80%;">
                                ${message}
                             </div>`;

            if (settings.show_timestamp) {
                messageHTML += `<div class="timestamp" style="font-size:0.8em;color:#888;margin-top:2px;text-align:right">
                                ${formatTimestamp()}
                              </div>`;
            }

            userMsgDiv.innerHTML = messageHTML;
            chatMessages.appendChild(userMsgDiv);

            // Clear input
            textInput.value = '';

            // Show typing indicator
            const typingDiv = document.createElement('div');
            typingDiv.className = 'botTyping';
            typingDiv.innerHTML = '<div class="bounce1"></div><div class="bounce2"></div><div class="bounce3"></div>';
            chatMessages.appendChild(typingDiv);

            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Send message to API
            fetch(`${settings.baseUrl}${settings.apiEndpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: settings.userId,
                }),
            })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                const typingIndicator = chatMessages.querySelector('.botTyping');
                if (typingIndicator) {
                    typingIndicator.remove();
                }

                // Add bot response
                const botResponse = document.createElement('div');
                botResponse.style.marginBottom = '10px';

                let responseHTML = `<img class="botAvatar" src="${settings.bot_avatar}" style="width:30px;height:30px;border-radius:50%;margin-right:10px;">
                                  <div class="botMsg" style="background:${settings.theme === 'dark' ? '#40444b' : 'white'};
                                                           color:${settings.theme === 'dark' ? '#fff' : '#000'};
                                                           padding:10px;
                                                           border-radius:10px;
                                                           max-width:80%;">
                                    ${data.response}
                                  </div>`;

                if (settings.show_timestamp) {
                    responseHTML += `<div class="timestamp" style="font-size:0.8em;color:#888;margin-top:2px">
                                    ${formatTimestamp()}
                                   </div>`;
                }

                botResponse.innerHTML = responseHTML;
                chatMessages.appendChild(botResponse);

                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(error => {
                console.error('Error:', error);
                // Remove typing indicator
                const typingIndicator = chatMessages.querySelector('.botTyping');
                if (typingIndicator) {
                    typingIndicator.remove();
                }

                // Show error message
                const errorDiv = document.createElement('div');
                errorDiv.style.marginBottom = '10px';
                errorDiv.innerHTML = `<img class="botAvatar" src="${settings.bot_avatar}" style="width:30px;height:30px;border-radius:50%;margin-right:10px;">
                                    <div class="botMsg" style="background:${settings.theme === 'dark' ? '#40444b' : 'white'};
                                                             color:red;
                                                             padding:10px;
                                                             border-radius:10px;
                                                             max-width:80%;">
                                        Sorry, I'm having trouble connecting right now. Please try again later.
                                    </div>`;
                
                if (settings.show_timestamp) {
                    errorDiv.innerHTML += `<div class="timestamp" style="font-size:0.8em;color:#888;margin-top:2px">
                                            ${formatTimestamp()}
                                         </div>`;
                }

                chatMessages.appendChild(errorDiv);

                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });
        }
    };

    sendButton.addEventListener('click', sendMessage);
    textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}
