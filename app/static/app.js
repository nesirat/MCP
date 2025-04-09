// API endpoints
const API_BASE_URL = '/api/v1';
const ENDPOINTS = {
    register: `${API_BASE_URL}/register`,
    token: `${API_BASE_URL}/token`,
    apiKeys: `${API_BASE_URL}/api-keys`
};

// State management
let currentToken = localStorage.getItem('token');

// DOM Elements
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const apiKeysSection = document.getElementById('apiKeysSection');
const createApiKeyForm = document.getElementById('createApiKeyForm');
const apiKeysList = document.getElementById('apiKeysList');

// Form Elements
const loginFormElement = document.getElementById('loginFormElement');
const registerFormElement = document.getElementById('registerFormElement');
const createApiKeyFormElement = document.getElementById('createApiKeyFormElement');

// Navigation Elements
const loginNav = document.getElementById('loginNav');
const registerNav = document.getElementById('registerNav');
const logoutNav = document.getElementById('logoutNav');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    if (currentToken) {
        showApiKeysSection();
        loadApiKeys();
    } else {
        showLoginForm();
    }

    loginFormElement.addEventListener('submit', handleLogin);
    registerFormElement.addEventListener('submit', handleRegister);
    createApiKeyFormElement.addEventListener('submit', handleCreateApiKey);
});

// Form Handlers
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch(ENDPOINTS.token, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        const data = await response.json();
        currentToken = data.access_token;
        localStorage.setItem('token', currentToken);
        showApiKeysSection();
        loadApiKeys();
    } catch (error) {
        showAlert('Login failed. Please check your credentials.', 'danger');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;

    try {
        const response = await fetch(ENDPOINTS.register, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            throw new Error('Registration failed');
        }

        showAlert('Registration successful! Please login.', 'success');
        showLoginForm();
    } catch (error) {
        showAlert('Registration failed. Please try again.', 'danger');
    }
}

async function handleCreateApiKey(e) {
    e.preventDefault();
    const name = document.getElementById('apiKeyName').value;
    const description = document.getElementById('apiKeyDescription').value;

    try {
        const response = await fetch(ENDPOINTS.apiKeys, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, description })
        });

        if (!response.ok) {
            throw new Error('Failed to create API key');
        }

        const data = await response.json();
        showAlert('API key created successfully!', 'success');
        hideCreateApiKeyForm();
        loadApiKeys();
    } catch (error) {
        showAlert('Failed to create API key. Please try again.', 'danger');
    }
}

// UI Functions
function showLoginForm() {
    hideAllForms();
    loginForm.classList.remove('d-none');
    loginNav.classList.remove('d-none');
    registerNav.classList.remove('d-none');
    logoutNav.classList.add('d-none');
}

function showRegisterForm() {
    hideAllForms();
    registerForm.classList.remove('d-none');
}

function showApiKeysSection() {
    hideAllForms();
    apiKeysSection.classList.remove('d-none');
    loginNav.classList.add('d-none');
    registerNav.classList.add('d-none');
    logoutNav.classList.remove('d-none');
}

function showCreateApiKeyForm() {
    createApiKeyForm.classList.remove('d-none');
}

function hideCreateApiKeyForm() {
    createApiKeyForm.classList.add('d-none');
    createApiKeyFormElement.reset();
}

function hideAllForms() {
    loginForm.classList.add('d-none');
    registerForm.classList.add('d-none');
    apiKeysSection.classList.add('d-none');
    createApiKeyForm.classList.add('d-none');
}

function logout() {
    currentToken = null;
    localStorage.removeItem('token');
    showLoginForm();
}

// API Functions
async function loadApiKeys() {
    try {
        const response = await fetch(ENDPOINTS.apiKeys, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load API keys');
        }

        const apiKeys = await response.json();
        displayApiKeys(apiKeys);
    } catch (error) {
        showAlert('Failed to load API keys. Please try again.', 'danger');
    }
}

async function deleteApiKey(keyId) {
    try {
        const response = await fetch(`${ENDPOINTS.apiKeys}/${keyId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to delete API key');
        }

        showAlert('API key deleted successfully!', 'success');
        loadApiKeys();
    } catch (error) {
        showAlert('Failed to delete API key. Please try again.', 'danger');
    }
}

async function revokeApiKey(keyId) {
    try {
        const response = await fetch(`${ENDPOINTS.apiKeys}/${keyId}/revoke`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to revoke API key');
        }

        showAlert('API key revoked successfully!', 'success');
        loadApiKeys();
    } catch (error) {
        showAlert('Failed to revoke API key. Please try again.', 'danger');
    }
}

// Helper Functions
function displayApiKeys(apiKeys) {
    apiKeysList.innerHTML = apiKeys.map(key => `
        <div class="api-key-item">
            <h5>${key.name}</h5>
            ${key.description ? `<p>${key.description}</p>` : ''}
            <div class="key">${key.key}</div>
            <div class="actions">
                <button class="btn btn-danger" onclick="deleteApiKey(${key.id})">Delete</button>
                <button class="btn btn-warning" onclick="revokeApiKey(${key.id})">Revoke</button>
            </div>
        </div>
    `).join('');
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.card'));
    setTimeout(() => alertDiv.remove(), 5000);
} 