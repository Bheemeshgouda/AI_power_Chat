// Global Variables
let currentSlides = [];
let chatHistory = [];

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const generatePptBtn = document.getElementById('generatePptBtn');
const clearSlidesBtn = document.getElementById('clearSlidesBtn');
const slidesPreview = document.getElementById('slidesPreview');
const loadingOverlay = document.getElementById('loadingOverlay');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    adjustTextareaHeight();
});

// Event Listeners
function setupEventListeners() {
    // Send message on button click
    sendBtn.addEventListener('click', sendMessage);
    
    // Send message on Enter key (Shift+Enter for new line)
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-resize textarea
    userInput.addEventListener('input', adjustTextareaHeight);
    
    // Clear chat
    clearChatBtn.addEventListener('click', clearChat);
    
    // Generate PowerPoint
    generatePptBtn.addEventListener('click', generatePowerPoint);
    
    // Clear slides
    clearSlidesBtn.addEventListener('click', clearSlides);
}

// Adjust textarea height dynamically
function adjustTextareaHeight() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
}

// Send Message
async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Clear input
    userInput.value = '';
    adjustTextareaHeight();
    
    // Show loading
    showLoading();
    
    try {
        // Determine if this is an edit or new generation
        const isEdit = detectEditIntent(message);
        
        let response;
        if (isEdit && currentSlides.length > 0) {
            // Send to update endpoint
            response = await fetch('/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: message,
                    slides: currentSlides
                })
            });
        } else {
            // Send to chat endpoint
            response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: message
                })
            });
        }
        
        if (!response.ok) {
            throw new Error('Failed to get response from server');
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Update slides
        currentSlides = data.slides || [];
        
        // Add AI response to chat
        const aiMessage = data.message || 'Slides generated successfully!';
        addMessageToChat(aiMessage, 'ai');
        
        // Update slides preview
        updateSlidesPreview();
        
        // Enable buttons
        generatePptBtn.disabled = false;
        clearSlidesBtn.disabled = false;
        
    } catch (error) {
        console.error('Error:', error);
        addMessageToChat(`Sorry, an error occurred: ${error.message}`, 'ai', true);
    } finally {
        hideLoading();
    }
}

// Detect if message is an edit intent
function detectEditIntent(message) {
    const editKeywords = ['edit', 'update', 'change', 'modify', 'replace', 'add to', 'remove from'];
    const lowerMessage = message.toLowerCase();
    return editKeywords.some(keyword => lowerMessage.includes(keyword));
}

// Add message to chat
function addMessageToChat(message, sender, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-bubble ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = sender === 'user' ? 'user-avatar' : 'ai-avatar';
    avatar.innerHTML = sender === 'user' ? '<i class="bi bi-person-fill"></i>' : '<i class="bi bi-robot"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    if (isError) {
        content.innerHTML = `<p style="color: #ef4444;"><i class="bi bi-exclamation-triangle"></i> ${escapeHtml(message)}</p>`;
    } else {
        content.innerHTML = `<p>${escapeHtml(message)}</p>`;
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Add to history
    chatHistory.push({ message, sender, timestamp: new Date() });
}

// Update slides preview
function updateSlidesPreview() {
    if (currentSlides.length === 0) {
        slidesPreview.innerHTML = `
            <div class="no-slides">
                <i class="bi bi-file-earmark-plus"></i>
                <p>No slides yet</p>
                <small>Start chatting to create your presentation</small>
            </div>
        `;
        return;
    }
    
    slidesPreview.innerHTML = '';
    
    currentSlides.forEach((slide, index) => {
        const slideCard = document.createElement('div');
        slideCard.className = 'slide-card';
        slideCard.dataset.index = index;
        
        let contentHtml = '';
        if (Array.isArray(slide.content)) {
            contentHtml = '<ul>' + slide.content.map(point => `<li>${escapeHtml(point)}</li>`).join('') + '</ul>';
        } else if (typeof slide.content === 'string') {
            contentHtml = `<p>${escapeHtml(slide.content)}</p>`;
        }
        
        // Add image indicator if slide has image
        let imageIndicator = '';
        if (slide.has_image && slide.image_url) {
            imageIndicator = '<div class="slide-image-indicator"><i class="bi bi-image-fill"></i> Has Image</div>';
        }
        
        slideCard.innerHTML = `
            <div class="slide-number">${index + 1}</div>
            <h6>${escapeHtml(slide.title || 'Untitled Slide')}</h6>
            ${contentHtml}
            ${imageIndicator}
        `;
        
        slideCard.addEventListener('click', () => {
            document.querySelectorAll('.slide-card').forEach(card => card.classList.remove('active'));
            slideCard.classList.add('active');
        });
        
        slidesPreview.appendChild(slideCard);
    });
}

// Generate PowerPoint
function generatePowerPoint() {
    if (currentSlides.length === 0) {
        alert('No slides to generate. Please create slides first.');
        return;
    }
    
    showLoading();
    
    try {
        // Create new presentation
        let pptx = new PptxGenJS();
        
        // Set presentation properties
        pptx.author = 'AI PowerPoint Generator';
        pptx.company = 'Gemini AI';
        pptx.title = 'AI Generated Presentation';
        pptx.subject = 'Auto-generated presentation';
        
        // Add slides
        currentSlides.forEach((slideData, index) => {
            let slide = pptx.addSlide();
            
            // Check if slide should have an image
            const hasImage = slideData.has_image && slideData.image_url;
            const imagePosition = slideData.image_position || 'right';
            
            // Add slide number
            slide.addText(`${index + 1}`, {
                x: 0.5,
                y: 0.3,
                w: 0.5,
                h: 0.3,
                fontSize: 12,
                color: '666666',
                align: 'left'
            });
            
            // Add title
            slide.addText(slideData.title || 'Untitled Slide', {
                x: 0.5,
                y: 0.7,
                w: 9,
                h: 0.8,
                fontSize: 32,
                bold: true,
                color: '1F4788',
                align: 'left'
            });
            
            // Calculate layout based on image presence and position
            let contentX, contentY, contentW, contentH;
            let imgX, imgY, imgW, imgH;
            
            if (hasImage) {
                if (imagePosition === 'top') {
                    // Image on top, content below
                    imgX = 2.5;
                    imgY = 1.7;
                    imgW = 5;
                    imgH = 2.8;
                    
                    contentX = 0.7;
                    contentY = 4.8;
                    contentW = 8.6;
                    contentH = 2;
                } else if (imagePosition === 'bottom') {
                    // Content on top, image below
                    contentX = 0.7;
                    contentY = 1.7;
                    contentW = 8.6;
                    contentH = 2.5;
                    
                    imgX = 2.5;
                    imgY = 4.5;
                    imgW = 5;
                    imgH = 2.5;
                } else if (imagePosition === 'left') {
                    // Image on left, content on right
                    imgX = 0.5;
                    imgY = 1.7;
                    imgW = 4.2;
                    imgH = 5;
                    
                    contentX = 5;
                    contentY = 1.7;
                    contentW = 4.5;
                    contentH = 5;
                } else {
                    // Default: Image on right, content on left
                    contentX = 0.7;
                    contentY = 1.7;
                    contentW = 4.5;
                    contentH = 5;
                    
                    imgX = 5.5;
                    imgY = 1.7;
                    imgW = 4;
                    imgH = 5;
                }
            } else {
                // No image - use full width for content
                contentX = 0.7;
                contentY = 1.7;
                contentW = 8.6;
                contentH = 5;
            }
            
            // Add content
            if (Array.isArray(slideData.content) && slideData.content.length > 0) {
                const bulletPoints = slideData.content.map(point => ({
                    text: point,
                    options: { bullet: true, fontSize: 16, color: '333333' }
                }));
                
                slide.addText(bulletPoints, {
                    x: contentX,
                    y: contentY,
                    w: contentW,
                    h: contentH,
                    fontSize: 16,
                    color: '333333',
                    valign: 'top'
                });
            } else if (typeof slideData.content === 'string') {
                slide.addText(slideData.content, {
                    x: contentX,
                    y: contentY,
                    w: contentW,
                    h: contentH,
                    fontSize: 16,
                    color: '333333',
                    valign: 'top'
                });
            }
            
            // Add image if available
            if (hasImage) {
                const imageUrl = window.location.origin + slideData.image_url;
                
                slide.addImage({
                    path: imageUrl,
                    x: imgX,
                    y: imgY,
                    w: imgW,
                    h: imgH
                });
            }
            
            // Add footer
            slide.addText('Generated by AI PowerPoint Assistant', {
                x: 0.5,
                y: 7,
                w: 9,
                h: 0.3,
                fontSize: 10,
                color: '999999',
                align: 'center'
            });
        });
        
        // Generate and download
        const fileName = `AI_Presentation_${new Date().toISOString().slice(0, 10)}.pptx`;
        pptx.writeFile({ fileName: fileName });
        
        // Show success message
        addMessageToChat(`✅ PowerPoint generated successfully! File: ${fileName}`, 'ai');
        
    } catch (error) {
        console.error('Error generating PowerPoint:', error);
        addMessageToChat(`❌ Error generating PowerPoint: ${error.message}`, 'ai', true);
    } finally {
        hideLoading();
    }
}

// Clear chat
function clearChat() {
    if (!confirm('Are you sure you want to clear the chat history?')) {
        return;
    }
    
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <div class="ai-avatar">
                <i class="bi bi-robot"></i>
            </div>
            <div class="message-content">
                <h5>Welcome! 👋</h5>
                <p>I'm your AI PowerPoint assistant. I can help you create and edit presentations through simple conversation.</p>
                <p><strong>Try these commands:</strong></p>
                <ul>
                    <li>"Create 5 slides about Artificial Intelligence in Education"</li>
                    <li>"Add a slide about future trends in AI"</li>
                    <li>"Edit slide 2: change the title to 'AI in Modern Learning'"</li>
                    <li>"Update slide 3 - add a point about 'Ethical Concerns'"</li>
                </ul>
            </div>
        </div>
    `;
    
    chatHistory = [];
}

// Clear slides
function clearSlides() {
    if (!confirm('Are you sure you want to clear all slides?')) {
        return;
    }
    
    currentSlides = [];
    updateSlidesPreview();
    generatePptBtn.disabled = true;
    clearSlidesBtn.disabled = true;
    
    addMessageToChat('All slides cleared. You can start creating a new presentation.', 'ai');
}

// Show loading overlay
function showLoading() {
    loadingOverlay.classList.add('active');
}

// Hide loading overlay
function hideLoading() {
    loadingOverlay.classList.remove('active');
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-focus input on load
userInput.focus();
