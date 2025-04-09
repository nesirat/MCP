// State management
let currentUser = null;
let accessToken = localStorage.getItem('accessToken');
let sessionTimeout = null;
let rememberMe = false;

// DOM Elements
const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');
const loginForm = document.getElementById('loginForm');
const loginFormElement = document.getElementById('loginFormElement');
const apiKeysSection = document.getElementById('apiKeysSection');
const createKeyBtn = document.getElementById('createKeyBtn');
const createKeyModal = document.getElementById('createKeyModal');
const createKeyForm = document.getElementById('createKeyForm');
const cancelCreateKey = document.getElementById('cancelCreateKey');
const apiKeysList = document.getElementById('apiKeysList');
const rememberMeCheckbox = document.getElementById('rememberMe');

// Event Listeners
loginBtn.addEventListener('click', () => {
    loginForm.classList.remove('hidden');
    loginBtn.classList.add('hidden');
});

loginFormElement.addEventListener('submit', handleLogin);
logoutBtn.addEventListener('click', handleLogout);
createKeyBtn.addEventListener('click', () => {
    createKeyModal.classList.remove('hidden');
    createKeyModal.classList.add('modal-enter');
});
cancelCreateKey.addEventListener('click', () => {
    createKeyModal.classList.add('hidden');
    createKeyModal.classList.remove('modal-enter');
});
createKeyForm.addEventListener('submit', handleCreateKey);

// Session timeout functions
function resetSessionTimeout() {
    if (sessionTimeout) {
        clearTimeout(sessionTimeout);
    }
    if (!rememberMe) {
        sessionTimeout = setTimeout(handleSessionTimeout, 5 * 60 * 1000); // 5 minutes
    }
}

function handleSessionTimeout() {
    handleLogout();
    showToast('Session expired due to inactivity', 'error');
}

// Add event listeners for user activity
document.addEventListener('mousemove', resetSessionTimeout);
document.addEventListener('keypress', resetSessionTimeout);
document.addEventListener('click', resetSessionTimeout);

// Functions
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    rememberMe = rememberMeCheckbox.checked;

    try {
        const response = await fetch('/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}&remember_me=${rememberMe}`,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Login failed');
        }

        const data = await response.json();
        accessToken = data.access_token;
        
        if (rememberMe) {
            localStorage.setItem('accessToken', accessToken);
        } else {
            sessionStorage.setItem('accessToken', accessToken);
        }
        
        // Update UI
        loginForm.classList.add('hidden');
        loginBtn.classList.remove('hidden');
        document.getElementById('userSection').classList.remove('hidden');
        document.getElementById('loginSection').classList.add('hidden');
        
        // Load API keys
        await loadApiKeys();
        apiKeysSection.classList.remove('hidden');
        
        // Reset session timeout
        resetSessionTimeout();
        
        showToast('Login successful', 'success');
    } catch (error) {
        console.error('Login error:', error);
        showToast('Login failed: ' + error.message, 'error');
    }
}

async function handleLogout() {
    accessToken = null;
    localStorage.removeItem('accessToken');
    sessionStorage.removeItem('accessToken');
    currentUser = null;
    
    if (sessionTimeout) {
        clearTimeout(sessionTimeout);
        sessionTimeout = null;
    }
    
    // Update UI
    document.getElementById('userSection').classList.add('hidden');
    document.getElementById('loginSection').classList.remove('hidden');
    apiKeysSection.classList.add('hidden');
    apiKeysList.innerHTML = '';
    
    showToast('Logged out successfully', 'success');
}

async function handleCreateKey(e) {
    e.preventDefault();
    const name = document.getElementById('keyName').value;
    const description = document.getElementById('keyDescription').value;

    if (!accessToken) {
        console.error('No access token found');
        showToast('Please log in first', 'error');
        return;
    }

    try {
        console.log('Creating API key with token:', accessToken ? 'Present' : 'Missing');
        const response = await fetch('/api-keys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`,
            },
            body: JSON.stringify({ name, description }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to create API key');
        }

        const data = await response.json();
        
        // Add new key to the list
        addApiKeyToList(data);
        
        // Close modal and reset form
        createKeyModal.classList.add('hidden');
        createKeyModal.classList.remove('modal-enter');
        createKeyForm.reset();
        
        showToast('API key created successfully', 'success');
    } catch (error) {
        console.error('Create key error:', error);
        showToast('Failed to create API key: ' + error.message, 'error');
    }
}

async function loadApiKeys() {
    if (!accessToken) {
        console.error('No access token found');
        showToast('Please log in first', 'error');
        return;
    }

    try {
        console.log('Loading API keys with token:', accessToken ? 'Present' : 'Missing');
        const response = await fetch('/api-keys', {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            },
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to load API keys');
        }

        const apiKeys = await response.json();
        apiKeysList.innerHTML = '';
        apiKeys.forEach(key => addApiKeyToList(key));
    } catch (error) {
        console.error('Load keys error:', error);
        showToast('Failed to load API keys: ' + error.message, 'error');
    }
}

function addApiKeyToList(key) {
    const keyElement = document.createElement('div');
    keyElement.className = 'api-key-card bg-white p-4 rounded-lg shadow';
    
    const statusColor = key.is_active ? 'text-green-500' : 'text-red-500';
    const statusIcon = key.is_active ? 'check-circle' : 'times-circle';
    
    keyElement.innerHTML = `
        <div class="flex justify-between items-start">
            <div>
                <h3 class="text-lg font-medium">${key.name}</h3>
                <p class="text-sm text-gray-500">${key.description || 'No description'}</p>
                <p class="text-xs text-gray-400 mt-1">Created: ${new Date(key.created_at).toLocaleDateString()}</p>
            </div>
            <div class="flex items-center space-x-2">
                <i class="fas fa-${statusIcon} ${statusColor}"></i>
                ${key.is_active ? `
                    <button onclick="revokeApiKey(${key.id})" class="text-red-600 hover:text-red-800">
                        <i class="fas fa-ban"></i>
                    </button>
                ` : ''}
                <button onclick="deleteApiKey(${key.id})" class="text-gray-600 hover:text-gray-800">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        <div class="mt-2">
            <code class="text-sm bg-gray-100 p-2 rounded block">${key.key}</code>
            <button onclick="copyToClipboard('${key.key}')" class="text-sm text-indigo-600 hover:text-indigo-800 mt-1">
                <i class="fas fa-copy"></i> Copy
            </button>
        </div>
    `;
    
    apiKeysList.appendChild(keyElement);
}

async function revokeApiKey(keyId) {
    if (!confirm('Are you sure you want to revoke this API key?')) {
        return;
    }

    try {
        const response = await fetch(`/api-keys/${keyId}/revoke`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to revoke API key');
        }

        await loadApiKeys();
        showToast('API key revoked successfully', 'success');
    } catch (error) {
        showToast('Failed to revoke API key: ' + error.message, 'error');
    }
}

async function deleteApiKey(keyId) {
    if (!confirm('Are you sure you want to delete this API key?')) {
        return;
    }

    try {
        const response = await fetch(`/api-keys/${keyId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to delete API key');
        }

        await loadApiKeys();
        showToast('API key deleted successfully', 'success');
    } catch (error) {
        showToast('Failed to delete API key: ' + error.message, 'error');
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard', 'success');
    }).catch(() => {
        showToast('Failed to copy to clipboard', 'error');
    });
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Check if user is already logged in
if (accessToken) {
    document.getElementById('userSection').classList.remove('hidden');
    document.getElementById('loginSection').classList.add('hidden');
    apiKeysSection.classList.remove('hidden');
    loadApiKeys();
}

// Password validation
function validatePassword(password) {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[@$!%*?&]/.test(password);
    
    const errors = [];
    if (password.length < minLength) {
        errors.push(`Password must be at least ${minLength} characters long`);
    }
    if (!hasUpperCase) {
        errors.push('Password must contain at least one uppercase letter');
    }
    if (!hasLowerCase) {
        errors.push('Password must contain at least one lowercase letter');
    }
    if (!hasNumbers) {
        errors.push('Password must contain at least one number');
    }
    if (!hasSpecialChar) {
        errors.push('Password must contain at least one special character (@$!%*?&)');
    }
    
    return errors;
}

// Add password validation to registration form
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    const passwordInput = document.getElementById('registerPassword');
    const passwordErrors = document.getElementById('passwordErrors');
    
    passwordInput.addEventListener('input', () => {
        const errors = validatePassword(passwordInput.value);
        if (errors.length > 0) {
            passwordErrors.innerHTML = errors.map(error => `<div class="text-red-500 text-sm">${error}</div>`).join('');
        } else {
            passwordErrors.innerHTML = '';
        }
    });
    
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('registerEmail').value;
        const password = passwordInput.value;
        
        const errors = validatePassword(password);
        if (errors.length > 0) {
            showToast('Please fix password requirements', 'error');
            return;
        }
        
        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Registration failed');
            }
            
            showToast('Registration successful', 'success');
            document.getElementById('registerModal').classList.add('hidden');
            registerForm.reset();
        } catch (error) {
            console.error('Registration error:', error);
            showToast('Registration failed: ' + error.message, 'error');
        }
    });
}

// Utility functions
const utils = {
    // Format date to local string
    formatDate: (date) => {
        return new Date(date).toLocaleDateString();
    },
    
    // Format datetime to local string
    formatDateTime: (date) => {
        return new Date(date).toLocaleString();
    },
    
    // Show success message
    showSuccess: (message) => {
        Swal.fire({
            icon: 'success',
            title: 'Success',
            text: message,
            timer: 3000,
            showConfirmButton: false
        });
    },
    
    // Show error message
    showError: (message) => {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: message
        });
    },
    
    // Show confirmation dialog
    showConfirm: (message) => {
        return Swal.fire({
            title: 'Are you sure?',
            text: message,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes'
        });
    },
    
    // Handle API errors
    handleApiError: (error) => {
        console.error('API Error:', error);
        let message = 'An error occurred';
        
        if (error.response) {
            if (error.response.data && error.response.data.detail) {
                message = error.response.data.detail;
            } else if (error.response.status === 401) {
                message = 'Session expired. Please login again.';
                setTimeout(() => window.location.href = '/login', 2000);
            } else if (error.response.status === 403) {
                message = 'You do not have permission to perform this action.';
            } else if (error.response.status === 404) {
                message = 'Resource not found.';
            }
        }
        
        utils.showError(message);
    }
};

// API client
const api = {
    // Base URL for API requests
    baseUrl: '/api/v1',
    
    // Default headers
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    
    // Get CSRF token from cookie
    getCsrfToken: () => {
        const name = 'csrf_token=';
        const decodedCookie = decodeURIComponent(document.cookie);
        const ca = decodedCookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) === 0) {
                return c.substring(name.length, c.length);
            }
        }
        return '';
    },
    
    // Make API request
    request: async (endpoint, options = {}) => {
        try {
            const url = `${api.baseUrl}${endpoint}`;
            const headers = {
                ...api.headers,
                ...options.headers
            };
            
            // Add CSRF token if available
            const csrfToken = api.getCsrfToken();
            if (csrfToken) {
                headers['X-CSRF-Token'] = csrfToken;
            }
            
            const response = await fetch(url, {
                ...options,
                headers,
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw response;
            }
            
            return await response.json();
        } catch (error) {
            utils.handleApiError(error);
            throw error;
        }
    },
    
    // GET request
    get: (endpoint, options = {}) => {
        return api.request(endpoint, {
            ...options,
            method: 'GET'
        });
    },
    
    // POST request
    post: (endpoint, data, options = {}) => {
        return api.request(endpoint, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    // PUT request
    put: (endpoint, data, options = {}) => {
        return api.request(endpoint, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    // DELETE request
    delete: (endpoint, options = {}) => {
        return api.request(endpoint, {
            ...options,
            method: 'DELETE'
        });
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add active class to current navigation item
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}); 