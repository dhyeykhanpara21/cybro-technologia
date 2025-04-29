/**
 * Key Detection Script
 * This script handles keyboard input detection and sends the key press events to the server.
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Function to log messages to console instead of status div
    function logMessage(message, isError = false) {
        if (isError) {
            console.error(message);
        } else {
            console.log(message);
        }
    }
    
    // Function to highlight control button when matching key is pressed
    function highlightMatchingButton(key) {
        // Find all control buttons
        const controlButtons = document.querySelectorAll('.control-btn');
        
        // Reset all buttons to default background
        controlButtons.forEach(btn => {
            btn.style.backgroundColor = '';
        });
        
        // Find the button with matching data-key attribute
        const matchingButton = document.querySelector(`.control-btn[data-key="${key.toLowerCase()}"]`);
        
        if (matchingButton) {
            // Change background color of the matching button
            matchingButton.style.backgroundColor = '#4CAF50'; // Green background
            
            // Reset the background after a short delay
            setTimeout(() => {
                matchingButton.style.backgroundColor = '';
            }, 300); // Reset after 300ms
            
            logMessage(`Highlighted button: ${key}`);
        }
    }
    
    // Add keydown event listener to the document
    document.addEventListener("keydown", function(event) {
        // Prevent default scrolling behavior for space key, arrow keys, and escape key
        if (event.key === " " || event.key === "Spacebar" || 
            event.key === "ArrowUp" || event.key === "ArrowDown" || 
            event.key === "ArrowLeft" || event.key === "ArrowRight" || 
            event.key === "Escape") {
            event.preventDefault();
        }
        
        logMessage(`Key pressed: ${event.key}`);
        
        // Highlight matching button
        highlightMatchingButton(event.key);
        
        fetch("/key-pressed", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ key: event.key })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(data.message);
            logMessage(`Server response: ${data.message}`);
        })
        .catch(error => {
            console.error('Error:', error);
            logMessage(`Error: ${error.message}`, true);
        });
    });
});