// Cambia esta URL por la de tu API en Render
const API_URL = "https://portfolio-ecommerce.onrender.com";
let accessToken = null;
let userEmail = null;
let productosDisponibles = [];
let carrito = [];
let publicKey = null;

function showLoading(btn, loading) {
  if (loading) {
    btn.disabled = true;
    btn.textContent = 'Cargando...';
  } else {
    btn.disabled = false;
    btn.textContent = btn.dataset.originalText;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Si ya hay token, muestra el formulario de pedidos
  if (accessToken) {
    document.getElementById("pedido-form").style.display = "block";
    document.getElementById("login-form").style.display = "none";
  }
});

// Función para obtener la clave pública
async function getPublicKey() {
  if (publicKey) return publicKey;
  
  try {
    const response = await fetch(`${API_URL}/api/users/public-key`, {
      credentials: 'include',
      mode: 'cors'
    });
    const data = await response.json();
    publicKey = data.key;
    return publicKey;
  } catch (error) {
    console.error('Error fetching public key:', error);
    throw new Error('Could not fetch encryption key');
  }
}

async function login() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const btn = document.querySelector('#login-form button');
  btn.dataset.originalText = btn.textContent;

  // Validación básica
  if (!email.match(/^\S+@\S+\.\S+$/)) {
    document.getElementById("login-error").textContent = "Introduce un email válido.";
    return;
  }
  if (!password || password.length < 4) {
    document.getElementById("login-error").textContent = "Introduce una contraseña válida.";
    return;
  }
  
  document.getElementById("login-error").textContent = "";
  showLoading(btn, true);
  
  try {    // Obtener la clave pública
    const pubKey = await getPublicKey();
    console.log('Received public key:', pubKey);  // Ver la clave pública completa
    
    // No eliminar los headers de la clave pública, son necesarios
    const cleanPubKey = pubKey.trim();
    console.log('Public key length:', cleanPubKey.length);
    
    // Cifrar la contraseña
    const encrypt = new JSEncrypt();
    encrypt.setPublicKey(cleanPubKey);
    
    // Log para debug
    console.log('Public key set:', encrypt.getPublicKey() ? 'OK' : 'Failed');
    
    // Asegurarnos de que la clave pública se configuró correctamente
    if (!encrypt.getPublicKey()) {
      console.error('Public key validation failed');
      throw new Error('Public key not set correctly');
    }
    
    // Cifrar la contraseña
    const encrypted_password = encrypt.encrypt(password);
    console.log('Public key format OK');
    
    // Si el cifrado falla
    if (!encrypted_password) {
      console.error('Encryption returned null or empty');
      throw new Error('Encryption failed');
    }
    
    // Verificar que el resultado es base64 válido
    try {
      atob(encrypted_password); // Intentar decodificar para validar
      console.log('Encrypted result is valid base64');
      console.log('Encrypted length:', encrypted_password.length);
    } catch (e) {
      console.error('Invalid base64 output:', e);
      throw new Error('Invalid encryption result');
    }
    // Enviar credenciales con la contraseña cifrada
    const response = await fetch(`${API_URL}/api/users/token`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      credentials: 'include',
      mode: 'cors',
      body: JSON.stringify({ 
        email, 
        encrypted_password: encrypted_password 
      })
    });

    const data = await response.json();
    if (response.ok && data.access) {
      accessToken = data.access;
      userEmail = email;
      document.getElementById("login-form").style.display = "none";
      document.getElementById("pedido-form").style.display = "block";
      document.getElementById("login-error").textContent = "";
      document.getElementById("user-info").style.display = "block";
      document.getElementById("logout-btn").style.display = "block";
      document.getElementById("user-info").textContent = `Usuario logueado: ${userEmail}`;
      // Limpiar campos
      document.getElementById("email").value = "";
      document.getElementById("password").value = "";
      await cargarProductos();
    } else {
      throw new Error(data.detail || "Error de autenticación");
    }
  } catch (error) {
    console.error('Error during login:', error);
    document.getElementById("login-error").textContent = error.message || "Error de red o autenticación";
  } finally {
    showLoading(btn, false);
  }
}

// Función para actualizar el token cuando expire
async function refreshAccessToken() {
  try {
    const response = await fetch(`${API_URL}/api/users/token/refresh`, {
      method: 'POST',
      credentials: 'include',  // Necesario para cookies
    });
    const data = await response.json();
    if (response.ok && data.access) {
      accessToken = data.access;
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

// Wrapper para fetch con manejo de token
async function fetchWithAuth(url, options = {}) {
  // Añadir headers por defecto
  options.headers = {
    ...options.headers,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {})
  };
  options.credentials = 'include';  // Siempre incluir cookies
  options.mode = 'cors';  // Siempre usar CORS

  try {
    let response = await fetch(url, options);
    
    // Si el token expiró (401), intentar refrescarlo
    if (response.status === 401) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        // Reintentar la petición original con el nuevo token
        options.headers['Authorization'] = `Bearer ${accessToken}`;
        response = await fetch(url, options);
      } else {
        // Si no se pudo refrescar, hacer logout
        logout();
        throw new Error('Session expired');
      }
    }
    
    return response;
  } catch (error) {
    console.error('Network error:', error);
    throw error;
  }
}

async function cargarProductos() {
  try {
    const response = await fetchWithAuth(`${API_URL}/api/products/`);
    const data = await response.json();
    
    productosDisponibles = data;
    const select = document.getElementById("producto-select");
    select.innerHTML = "";
    
    productosDisponibles.forEach(prod => {
      if (prod.stock_quantity > 0) {  // Solo mostrar productos con stock
        const option = document.createElement("option");
        option.value = prod.id;
        option.textContent = `${prod.title} (Stock: ${prod.stock_quantity})`;
        select.appendChild(option);
      }
    });
    
    if (select.options.length === 0) {
      document.getElementById("pedido-error").textContent = "No hay productos con stock disponible.";
    } else {
      document.getElementById("pedido-error").textContent = "";
    }
  } catch (error) {
    console.error('Error loading products:', error);
    document.getElementById("pedido-error").textContent = "Error al cargar productos";
  }
}

function agregarAlCarrito() {
  const select = document.getElementById("producto-select");
  const cantidad = parseInt(document.getElementById("producto-cantidad").value);
  const prodId = parseInt(select.value);
  
  if (!prodId || isNaN(cantidad) || cantidad <= 0) {
    document.getElementById("pedido-error").textContent = "Selecciona producto y cantidad válida.";
    return;
  }
  
  const prod = productosDisponibles.find(p => p.id === prodId);
  if (!prod) return;

  // Verificar stock disponible
  const existente = carrito.find(item => item.id === prodId);
  const cantidadTotal = (existente ? existente.stock_quantity : 0) + cantidad;

  if (cantidadTotal > prod.stock_quantity) {
    document.getElementById("pedido-error").textContent = `Solo hay ${prod.stock_quantity} unidades disponibles de este producto.`;
    return;
  }
  
  if (existente) {
    existente.stock_quantity += cantidad;
  } else {
    carrito.push({ id: prodId, name: prod.title, stock_quantity: cantidad });
  }
  
  mostrarCarrito();
  document.getElementById("pedido-error").textContent = "";
  document.getElementById("producto-cantidad").value = "1"; // Reset cantidad
}

function mostrarCarrito() {
  const ul = document.getElementById("carrito-lista");
  ul.innerHTML = "";
  carrito.forEach(item => {
    const li = document.createElement("li");
    li.textContent = `${item.title} (x${item.stock_quantity})`;
    ul.appendChild(li);
  });
}

async function comprarCarrito() {
  if (carrito.length === 0) {
    document.getElementById("pedido-error").textContent = "El carrito está vacío.";
    return;
  }

  const btn = document.querySelector('#pedido-form button[onclick="comprarCarrito()"]');
  btn.dataset.originalText = btn.textContent;
  showLoading(btn, true);
  
  try {
    const response = await fetchWithAuth(`${API_URL}/api/orders/`, {
      method: "POST",
      body: JSON.stringify({ 
        items: carrito.map(({id, stock_quantity}) => ({product_id: id, quantity: stock_quantity})) 
      })
    });

    const data = await response.json();
    if (response.ok && data.id) {
      document.getElementById("pedido-success").textContent = `Pedido creado con ID: ${data.id}`;
      document.getElementById("pedido-error").textContent = "";
      carrito = [];
      mostrarCarrito();
      await cargarProductos(); // Recargar productos para actualizar stock
    } else {
      throw new Error(data.detail || "Error al crear pedido");
    }
  } catch (error) {
    console.error('Error creating order:', error);
    document.getElementById("pedido-error").textContent = error.message || "Error de red";
    document.getElementById("pedido-success").textContent = "";
  } finally {
    showLoading(btn, false);
  }
}

function logout() {
  // Limpiar datos de sesión
  accessToken = null;
  userEmail = null;
  carrito = [];
  productosDisponibles = [];

  // Ocultar secciones de usuario logueado
  document.getElementById("pedido-form").style.display = "none";
  document.getElementById("user-info").style.display = "none";
  document.getElementById("logout-btn").style.display = "none";

  // Mostrar formulario de login
  document.getElementById("login-form").style.display = "block";
  document.getElementById("login-error").textContent = "";
  document.getElementById("pedido-error").textContent = "";
  document.getElementById("pedido-success").textContent = "";
}
