// Cambia esta URL por la de tu API en Render
const API_URL = "https://portfolio-ecommerce.onrender.com";
let accessToken = null;
let userEmail = null;
let productosDisponibles = [];
let carrito = [];

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

function login() {
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

  fetch(`${API_URL}/api/users/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
      showLoading(btn, false);
      if (status === 200 && data.access) {
        accessToken = data.access;
        userEmail = email;
        document.getElementById("login-form").style.display = "none";
        document.getElementById("pedido-form").style.display = "block";
        document.getElementById("login-error").textContent = "";
        document.getElementById("user-info").style.display = "block";
        document.getElementById("user-info").textContent = `Usuario logueado: ${userEmail}`;
        cargarProductos();
        // Limpiar campos
        document.getElementById("email").value = "";
        document.getElementById("password").value = "";
      } else {
        document.getElementById("login-error").textContent = data.detail || "Error de autenticación";
      }
    })
    .catch(() => {
      showLoading(btn, false);
      document.getElementById("login-error").textContent = "Error de red";
    });
}

function cargarProductos() {
  fetch(`${API_URL}/api/products/`, {
    headers: { "Authorization": `Bearer ${accessToken}` }
  })
    .then(res => res.json())
    .then(data => {
      productosDisponibles = data;
      const select = document.getElementById("producto-select");
      select.innerHTML = "";
      productosDisponibles.forEach(prod => {
        const option = document.createElement("option");
        option.value = prod.id;
        option.textContent = prod.name || `Producto ${prod.id}`;
        select.appendChild(option);
      });
    })
    .catch(() => {
      document.getElementById("pedido-error").textContent = "Error al cargar productos";
    });
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
  const existente = carrito.find(item => item.product_id === prodId);
  if (existente) {
    existente.quantity += cantidad;
  } else {
    carrito.push({ product_id: prodId, name: prod.name, quantity: cantidad });
  }
  mostrarCarrito();
  document.getElementById("pedido-error").textContent = "";
}

function mostrarCarrito() {
  const ul = document.getElementById("carrito-lista");
  ul.innerHTML = "";
  carrito.forEach(item => {
    const li = document.createElement("li");
    li.textContent = `${item.name} (x${item.quantity})`;
    ul.appendChild(li);
  });
}

function comprarCarrito() {
  if (carrito.length === 0) {
    document.getElementById("pedido-error").textContent = "El carrito está vacío.";
    return;
  }
  const btn = document.querySelector('#pedido-form button[onclick="comprarCarrito()"]');
  btn.dataset.originalText = btn.textContent;
  showLoading(btn, true);
  fetch(`${API_URL}/api/orders/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`
    },
    body: JSON.stringify({ items: carrito.map(({product_id, quantity}) => ({product_id, quantity})) })
  })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
      showLoading(btn, false);
      if (status === 200 && data.id) {
        document.getElementById("pedido-success").textContent = `Pedido creado con ID: ${data.id}`;
        document.getElementById("pedido-error").textContent = "";
        carrito = [];
        mostrarCarrito();
      } else {
        document.getElementById("pedido-error").textContent = data.detail || "Error al crear pedido";
        document.getElementById("pedido-success").textContent = "";
      }
    })
    .catch(() => {
      showLoading(btn, false);
      document.getElementById("pedido-error").textContent = "Error de red";
      document.getElementById("pedido-success").textContent = "";
    });
}
