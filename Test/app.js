document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show active tab pane
            tabPanes.forEach(pane => {
                pane.classList.remove('active');
                if (pane.id === tabId) {
                    pane.classList.add('active');
                }
            });
        });
    });
    
    // API base URL
    const API_BASE_URL = 'http://localhost:8000/api';
    
    // Response display elements
    const responseStatus = document.getElementById('response-status');
    const responseData = document.getElementById('response-data');
    
    // Helper function to display API response
    function displayResponse(response, error = false) {
        if (error) {
            responseStatus.className = 'error';
            responseStatus.textContent = `Error: ${response.status} ${response.statusText || ''}`;
        } else {
            responseStatus.className = 'success';
            responseStatus.textContent = `Success: ${response.status} ${response.statusText || ''}`;
        }
        
        if (typeof response.data === 'object') {
            responseData.textContent = JSON.stringify(response.data, null, 2);
        } else {
            responseData.textContent = response.data || '';
        }
    }
    
    // Helper function to make API calls
    async function callApi(endpoint, method = 'GET', data = null) {
        const url = `${API_BASE_URL}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            const responseData = await response.json();
            
            return {
                status: response.status,
                statusText: response.statusText,
                data: responseData
            };
        } catch (error) {
            console.error('API Error:', error);
            return {
                status: 500,
                statusText: error.message,
                data: { error: error.message }
            };
        }
    }
    
    // USER ENDPOINTS
    
    // Create User
    document.getElementById('create-user-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userData = {
            uid: document.getElementById('user-uid').value || null, // Make UID optional
            display_name: document.getElementById('user-display-name').value,
            email: document.getElementById('user-email').value,
            bio: document.getElementById('user-bio').value || null,
            profile_image_url: document.getElementById('user-profile-image').value || null
        };
        
        const response = await callApi('/users', 'POST', userData);
        displayResponse(response, response.status >= 400);
    });
    
    // Get User
    document.getElementById('get-user-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('get-user-id').value;
        const response = await callApi(`/users/${userId}`);
        displayResponse(response, response.status >= 400);
    });
    
    // Get User by Email
    document.getElementById('get-user-by-email-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = document.getElementById('user-email-lookup').value;
        const response = await callApi(`/users/by-email/${encodeURIComponent(email)}`);
        displayResponse(response, response.status >= 400);
    });

    // Update User
    document.getElementById('update-user-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('update-user-id').value;
        const userData = {
            display_name: document.getElementById('update-display-name').value || null,
            bio: document.getElementById('update-bio').value || null,
            profile_image_url: document.getElementById('update-profile-image').value || null
        };
        
        // Remove null values
        Object.keys(userData).forEach(key => {
            if (userData[key] === null) {
                delete userData[key];
            }
        });
        
        const response = await callApi(`/users/${userId}`, 'PUT', userData);
        displayResponse(response, response.status >= 400);
    });
    
    // Update User Interests
    document.getElementById('user-interests-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('interests-user-id').value;
        const interests = document.getElementById('user-interests').value.split(',').map(i => i.trim());
        
        const response = await callApi(`/users/${userId}/interests`, 'POST', { interests });
        displayResponse(response, response.status >= 400);
    });
    
    // Update User Location
    document.getElementById('user-location-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('location-user-id').value;
        const locationData = {
            latitude: parseFloat(document.getElementById('user-latitude').value),
            longitude: parseFloat(document.getElementById('user-longitude').value)
        };
        
        const response = await callApi(`/users/${userId}/location`, 'POST', locationData);
        displayResponse(response, response.status >= 400);
    });
    
    // Get User Events
    document.getElementById('user-events-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('events-user-id').value;
        const status = document.getElementById('events-status').value;
        
        let endpoint = `/users/${userId}/events`;
        if (status) {
            endpoint += `?status=${status}`;
        }
        
        const response = await callApi(endpoint);
        displayResponse(response, response.status >= 400);
    });
    
    // EVENT ENDPOINTS
    
    // Create Event
    document.getElementById('create-event-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Collect schedule items
        const scheduleItems = [];
        document.querySelectorAll('.schedule-item').forEach((item) => {
            // Get the actual index from the data attribute or from the element itself
            const itemIndex = item.querySelector('.remove-schedule-item').getAttribute('data-index');
            
            const title = document.getElementById(`schedule-title-${itemIndex}`).value;
            const speakerName = document.getElementById(`schedule-speaker-${itemIndex}`).value;
            const description = document.getElementById(`schedule-description-${itemIndex}`).value;
            const startTime = document.getElementById(`schedule-start-${itemIndex}`).value;
            const endTime = document.getElementById(`schedule-end-${itemIndex}`).value;
            
            if (title && startTime && endTime) {
                scheduleItems.push({
                    title: title,
                    speaker_name: speakerName || null,
                    description: description || null,
                    start_time: new Date(startTime).toISOString(),
                    end_time: new Date(endTime).toISOString()
                });
            }
        });
        
        const eventData = {
            title: document.getElementById('event-title').value,
            description: document.getElementById('event-description').value,
            start_time: new Date(document.getElementById('event-start').value).toISOString(),
            end_time: new Date(document.getElementById('event-end').value).toISOString(),
            venue: {
                name: document.getElementById('venue-name').value,
                address: document.getElementById('venue-address').value,
                latitude: parseFloat(document.getElementById('venue-lat').value),
                longitude: parseFloat(document.getElementById('venue-long').value)
            },
            category: document.getElementById('event-categories').value.split(',').map(c => c.trim()),
            image_url: document.getElementById('event-image').value || null,
            price: document.getElementById('event-price').value ? parseFloat(document.getElementById('event-price').value) : 0,
            organizer_name: document.getElementById('event-organizer').value,
            organizer_email: document.getElementById('event-organizer-email').value || null,
            organizer_phone: document.getElementById('event-organizer-phone').value || null,
            schedule: scheduleItems.length > 0 ? scheduleItems : null
        };
        
        const response = await callApi('/events', 'POST', eventData);
        displayResponse(response, response.status >= 400);
    });
    
    // Get Events
    document.getElementById('get-events-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const queryParams = [];
        
        const categories = document.getElementById('filter-categories').value;
        if (categories) {
            queryParams.push(`category=${encodeURIComponent(categories)}`);
        }
        
        const startDate = document.getElementById('filter-start-date').value;
        if (startDate) {
            queryParams.push(`start_date=${encodeURIComponent(new Date(startDate).toISOString())}`);
        }
        
        const endDate = document.getElementById('filter-end-date').value;
        if (endDate) {
            queryParams.push(`end_date=${encodeURIComponent(new Date(endDate).toISOString())}`);
        }
        
        const latitude = document.getElementById('filter-latitude').value;
        const longitude = document.getElementById('filter-longitude').value;
        const distance = document.getElementById('filter-distance').value;
        
        if (latitude && longitude) {
            queryParams.push(`latitude=${parseFloat(latitude)}`);
            queryParams.push(`longitude=${parseFloat(longitude)}`);
            queryParams.push(`distance=${parseFloat(distance)}`);
        }
        
        const freeOnly = document.getElementById('filter-free').checked;
        if (freeOnly) {
            queryParams.push('free_only=true');
        }
        
        let url = '/events';
        if (queryParams.length > 0) {
            url += `?${queryParams.join('&')}`;
        }
        
        const response = await callApi(url);
        displayResponse(response, response.status >= 400);
    });
    
    // Get Event by ID
    document.getElementById('get-event-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const eventId = document.getElementById('get-event-id').value;
        const response = await callApi(`/events/${eventId}`);
        displayResponse(response, response.status >= 400);
    });
    
    // RSVP to Event
    document.getElementById('event-rsvp-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const eventId = document.getElementById('rsvp-event-id').value;
        const userId = document.getElementById('rsvp-user-id').value;
        
        // Status is now fixed to "attending"
        const rsvpData = {
            status: "attending"
        };
        
        // Pass user_id as a query parameter
        const response = await callApi(`/events/${eventId}/rsvp?user_id=${userId}`, 'POST', rsvpData);
        displayResponse(response, response.status >= 400);
    });
    
    // Get Event Attendees
    document.getElementById('event-attendees-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const eventId = document.getElementById('attendees-event-id').value;
        const status = document.getElementById('attendees-status').value;
        
        let endpoint = `/events/${eventId}/attendees`;
        if (status) {
            endpoint += `?status=${status}`;
        }
        
        const response = await callApi(endpoint);
        displayResponse(response, response.status >= 400);
    });
    
    // Get Event Recommendations
    document.getElementById('event-recommendations-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('rec-user-id').value;
        const latitude = document.getElementById('rec-latitude').value;
        const longitude = document.getElementById('rec-longitude').value;
        const distance = document.getElementById('rec-distance').value;
        const limit = document.getElementById('rec-limit').value || 10;
        
        const queryParams = [
            `latitude=${parseFloat(latitude)}`,
            `longitude=${parseFloat(longitude)}`,
            `distance=${parseFloat(distance)}`,
            `limit=${parseInt(limit)}`
        ];
        
        const endpoint = `/events/recommendations/${userId}?${queryParams.join('&')}`;
        const response = await callApi(endpoint);
        displayResponse(response, response.status >= 400);
    });
    
    // CONNECTION ENDPOINTS
    
    // Send Connection Request
    document.getElementById('connection-request-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const fromUserId = document.getElementById('from-user-id').value;
        const toUserId = document.getElementById('to-user-id').value;
        
        const connectionData = {
            from_user_id: fromUserId,
            to_user_id: toUserId
        };
        
        const response = await callApi(`/connections/request`, 'POST', connectionData);
        displayResponse(response, response.status >= 400);
    });
    
    // Respond to Connection Request
    document.getElementById('connection-response-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('responder-user-id').value;
        const senderId = document.getElementById('sender-user-id').value;
        const status = document.getElementById('connection-response-status').value;
        
        const responseData = {
            request_id: senderId, // ID of the user who sent the request
            user_id: userId,      // ID of the user responding
            status: status
        };
        
        // Always use "find" to tell the backend to find the connection based on user IDs
        const response = await callApi(`/connections/respond/find`, 'POST', responseData);
        displayResponse(response, response.status >= 400);
    });
    
    // Get User Connections
    document.getElementById('user-connections-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('connections-user-id').value;
        const status = document.getElementById('connections-status').value;
        
        let endpoint = `/connections/user/${userId}`;
        if (status) {
            endpoint += `?status=${status}`;
        }
        
        const response = await callApi(endpoint);
        displayResponse(response, response.status >= 400);
    });
    
    // Get Pending Connection Requests
    document.getElementById('pending-requests-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('pending-requests-user-id').value;
        const endpoint = `/connections/pending-requests?user_id=${userId}`;
        
        const response = await callApi(endpoint);
        displayResponse(response, response.status >= 400);
    });
    
    // Get Connection Recommendations
    document.getElementById('connection-recommendations-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('conn-rec-user-id').value;
        const limit = document.getElementById('conn-rec-limit').value;
        
        const endpoint = `/connections/recommendations/${userId}?limit=${limit}`;
        const response = await callApi(endpoint);
        displayResponse(response, response.status >= 400);
    });
    
    // Get Event Connection Recommendations
    document.getElementById('event-connections-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const eventId = document.getElementById('event-conn-event-id').value;
        const userId = document.getElementById('event-conn-user-id').value;
        const limit = document.getElementById('event-conn-limit').value;
        
        const endpoint = `/connections/event/${eventId}/user/${userId}?limit=${limit}`;
        const response = await callApi(endpoint);
        displayResponse(response, response.status >= 400);
    });
    
    // Get Connections Activity
    document.getElementById('connections-activity-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('activity-user-id').value;
        const limit = document.getElementById('activity-limit').value || 20;
        const days = document.getElementById('activity-days').value || 30;
        
        const endpoint = `/connections/activity/${userId}?limit=${limit}&days=${days}`;
        
        const response = await callApi(endpoint);
        displayResponse(response, response.status >= 400);
    });
    
    // Get User Feed (Pending Requests + Activities)
    document.getElementById('user-feed-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('feed-user-id').value;
        const limit = document.getElementById('feed-limit').value || 20;
        
        const endpoint = `/connections/feed/${userId}?limit=${limit}`;
        
        const response = await callApi(endpoint);
        displayResponse(response, response.status >= 400);
    });
    
    // FEEDBACK ENDPOINTS
    
    // Create Feedback
    document.getElementById('create-feedback-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const eventId = document.getElementById('feedback-event-id').value;
        const userId = document.getElementById('feedback-user-id').value;
        const feedbackData = {
            rating: parseInt(document.getElementById('feedback-rating').value),
            comment: document.getElementById('feedback-comment').value || null
        };
        
        // Pass user_id as a query parameter
        const response = await callApi(`/feedback/${eventId}?user_id=${userId}`, 'POST', feedbackData);
        displayResponse(response, response.status >= 400);
    });
    
    // Get All Event Feedback
    document.getElementById('get-event-feedback-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const eventId = document.getElementById('get-feedback-event-id').value;
        const response = await callApi(`/feedback/${eventId}`);
        displayResponse(response, response.status >= 400);
    });
    
    // Get User Feedback for Event
    document.getElementById('get-user-event-feedback-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const eventId = document.getElementById('user-feedback-event-id').value;
        const userId = document.getElementById('user-feedback-user-id').value;
        const response = await callApi(`/feedback/${eventId}/user/${userId}`);
        displayResponse(response, response.status >= 400);
    });
    
    // Get All User Feedback
    document.getElementById('get-all-user-feedback-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('all-user-feedback-id').value;
        const response = await callApi(`/feedback/user/${userId}`);
        displayResponse(response, response.status >= 400);
    });
    
    // Update Feedback
    document.getElementById('update-feedback-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const eventId = document.getElementById('update-feedback-event-id').value;
        const userId = document.getElementById('update-feedback-user-id').value;
        const feedbackData = {
            rating: parseInt(document.getElementById('update-feedback-rating').value),
            comment: document.getElementById('update-feedback-comment').value || null
        };
        
        const response = await callApi(`/feedback/${eventId}/user/${userId}`, 'PUT', feedbackData);
        displayResponse(response, response.status >= 400);
    });
    
    // Delete Feedback
    document.getElementById('delete-feedback-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const eventId = document.getElementById('delete-feedback-event-id').value;
        const userId = document.getElementById('delete-feedback-user-id').value;
        const response = await callApi(`/feedback/${eventId}/user/${userId}`, 'DELETE');
        displayResponse(response, response.status >= 400);
    });

    // Initialize schedule items counter
    let scheduleItemCount = 0;

    // Add schedule item button handler
    document.getElementById('add-schedule-item').addEventListener('click', function() {
        const container = document.getElementById('schedule-items-container');
        const itemIndex = scheduleItemCount++;
        
        const itemDiv = document.createElement('div');
        itemDiv.className = 'schedule-item';
        itemDiv.innerHTML = `
            <h4>Schedule Item #${itemIndex + 1}</h4>
            <div class="form-group">
                <label for="schedule-title-${itemIndex}">Title:</label>
                <input type="text" id="schedule-title-${itemIndex}" required>
            </div>
            <div class="form-group">
                <label for="schedule-speaker-${itemIndex}">Speaker Name:</label>
                <input type="text" id="schedule-speaker-${itemIndex}">
            </div>
            <div class="form-group">
                <label for="schedule-description-${itemIndex}">Description:</label>
                <textarea id="schedule-description-${itemIndex}"></textarea>
            </div>
            <div class="form-group">
                <label for="schedule-start-${itemIndex}">Start Time:</label>
                <input type="datetime-local" id="schedule-start-${itemIndex}" required>
            </div>
            <div class="form-group">
                <label for="schedule-end-${itemIndex}">End Time:</label>
                <input type="datetime-local" id="schedule-end-${itemIndex}" required>
            </div>
            <button type="button" class="remove-schedule-item" data-index="${itemIndex}">Remove</button>
        `;
        
        container.appendChild(itemDiv);
        
        // Add event listener to remove button
        itemDiv.querySelector('.remove-schedule-item').addEventListener('click', function() {
            container.removeChild(itemDiv);
        });
    });
});